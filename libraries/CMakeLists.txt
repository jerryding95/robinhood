if (UPDOWNRT_ENABLE_LIBRARIES)
    add_custom_target(libraries)
    set(UPDOWN_RUNTIME_INSTALL_DIR "updown")
    set(UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/libraries")

    set(UPDOWNSIMRT_PYTHON_LIBRARY_SRC
        UDMapShuffleReduce/Macro.py
        UDMapShuffleReduce/GlobalSync.py
        UDMapShuffleReduce/KeyValueSetTPL.py
        UDMapShuffleReduce/KVMapShuffleReduceTPL.py
        UDMapShuffleReduce/KVMSRMachineConfig.py
        UDMapShuffleReduce/ScratchpadCache.py
	    UDMapShuffleReduce/KVMapShuffleReduceTPL_basim.py
        SpMalloc/SpMalloc.py
    )


    # set(DEPS UDLibs UpDownBASimRuntimeStatic UpDownSimRuntimeStatic m)
    set(DEPS UpDownBASimRuntimeStatic UpDownSimRuntimeStatic m)

    foreach (LIBRARY_SRC ${UPDOWNSIMRT_LIBRARY_SRC})
        get_filename_component(BARENAME ${LIBRARY_SRC} NAME)
        string(REGEX REPLACE "[.]cpp$" "" LIBRARY_NAME ${BARENAME})
        add_executable(${LIBRARY_NAME} ${LIBRARY_SRC})
        target_link_libraries(${LIBRARY_NAME} ${DEPS})

        INSTALL(TARGETS ${LIBRARY_NAME}
            RUNTIME DESTINATION ${UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH}
        )
    endforeach()

    if(UPDOWN_ENABLE_BASIM)
        set(assem_prog "efa2bin.py")
        foreach(PYFILE IN LISTS UPDOWNSIMRT_PYTHON_LIBRARY_SRC2BIN)
            get_filename_component(PYFILEPATH ${PYFILE} REALPATH) 
            string(REGEX REPLACE "[.]py$" ".bin" PYBIN ${PYFILE})
	    get_filename_component(PYBINFILE ${PYBIN} NAME)
            add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${PYBINFILE}
                               COMMAND ${PYTHON_EXECUTABLE} ${assem_prog}
                               ARGS --efa ${PYFILEPATH} --outpath ${CMAKE_CURRENT_BINARY_DIR} --toplinker
                               WORKING_DIRECTORY ${UPDOWN_ASSEMBLER}
                               DEPENDS ${PYFILEPATH})
            list(APPEND UPDOWNSIMRT_PYTHON_UBENCH_BIN ${CMAKE_CURRENT_BINARY_DIR}/${PYBINFILE})
        endforeach()
        add_custom_target(UpdownSimRuntimePythonBin ALL DEPENDS ${UPDOWNSIMRT_PYTHON_UBENCH_BIN})
    endif()

    INSTALL(FILES ${UPDOWNSIMRT_PYTHON_LIBRARY_SRC} DESTINATION ${UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH})
    INSTALL(FILES ${UPDOWNSIMRT_PYTHON_UBENCH_BIN} DESTINATION ${UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH})

    # add_library(UDLibs dramalloc/dramalloc_service_core.cpp
    # dramalloc/dramalloc.hpp dramalloc/rtree.h dramalloc/rtree.cpp
    # dramalloc/alloc.h dramalloc/alloc.cpp)
endif(UPDOWNRT_ENABLE_LIBRARIES)
