if (UPDOWNRT_ENABLE_TESTS)

    message("GEM5 Mode set to ${FASTSIM}")
    
    set(GEM5_DEPS m5 rt)

    set(UPDOWNBASIMRT_TESTS_SRC 
        sendtest.cpp 
        sendpolicy_test.cpp 
        fork_join.cpp
        multilevel_fork_join.cpp
        dram_tests.cpp
    )

    # Once dramalloc works on gem5 this can be removed
    #if (UPDOWN_ENABLE_FASTSIM)
    #    list(APPEND UPDOWNBASIMRT_TESTS_SRC
    #        testDramalloc.cpp
    #    )
    #endif()

    include_directories(
        ../../libraries/dramalloc
    )
  
    set(UPDOWNBASIMRT_TESTS_PYSRC
        sendtest.py
        sendpolicy_test.py
        fork_join.py
        #testDramalloc.py
        multilevel_fork_join.py
        dram_tests_CHUNK1.py
        dram_tests_CHUNK2.py
        dram_tests_CHUNK3.py
        dram_tests_CHUNK4.py
        dram_tests_CHUNK5.py
        dram_tests_CHUNK6.py
        dram_tests_CHUNK7.py
        dram_tests_CHUNK8.py
    )

    set(UPDOWN_RUNTIME_TESTS_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/tests")

    if(UPDOWN_ENABLE_BASIM)
        set(assem_prog "efa2bin.py")
        foreach(PYFILE IN LISTS UPDOWNBASIMRT_TESTS_PYSRC)
            get_filename_component(PYFILEPATH ${PYFILE} REALPATH) 
            string(REGEX REPLACE "[.]py$" ".bin" PYBIN ${PYFILE})
	    get_filename_component(PYBINFILE ${PYBIN} NAME)
            add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${PYBINFILE}
                               COMMAND ${PYTHON_EXECUTABLE} ${assem_prog}
                               ARGS --efa ${PYFILEPATH} --outpath ${CMAKE_CURRENT_BINARY_DIR} --toplinker
                               WORKING_DIRECTORY ${UPDOWN_ASSEMBLER}
                               DEPENDS ${PYFILEPATH})            
            list(APPEND UPDOWNBASIMRT_TESTS_PYBIN ${CMAKE_CURRENT_BINARY_DIR}/${PYBINFILE})
        endforeach()
        add_custom_target(basimruntime_tests ALL DEPENDS ${UPDOWNBASIMRT_TESTS_PYBIN})
        add_dependencies(basimruntime_tests basimruntime)
    endif()

    if (DEFINED CMAKE_GEM5_BASE)
        #list(APPEND CMAKE_MODULE_PATH "../../../../include")
        include_directories(${GEM5_BASE_DIR}/include/)
        link_directories(${GEM5_BASE_DIR}/util/m5/build/x86/out)
        set(DEPS UDLibs UpDownBASimRuntimeStatic UpDownSimRuntimeStatic LaneElements ISAElements m rt m5)
        # set(DEPS UpDownBASimRuntimeStatic UpDownSimRuntimeStatic LaneElements ISAElements m rt m5)
    else ()
        set(DEPS UDLibs UpDownBASimRuntimeStatic UpDownSimRuntimeStatic m)
    endif ()

    foreach (TEST_SRC ${UPDOWNBASIMRT_TESTS_SRC})
        string(REGEX REPLACE "[.]cpp$" "" TEST_NAME ${TEST_SRC})
        add_executable(${TEST_NAME} ${TEST_SRC})
        target_link_libraries(${TEST_NAME} ${DEPS})

        INSTALL(TARGETS ${TEST_NAME}
            RUNTIME DESTINATION ${UPDOWN_RUNTIME_TESTS_INSTALL_PATH}
        )
    endforeach()

    INSTALL(FILES ${UPDOWNBASIMRT_TESTS_PYBIN} DESTINATION ${UPDOWN_RUNTIME_TESTS_INSTALL_PATH})

endif(UPDOWNRT_ENABLE_TESTS)
