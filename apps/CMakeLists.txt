include(CMakePrintHelpers)

if (UPDOWNRT_ENABLE_APPS)

    set(UPDOWN_RUNTIME_INSTALL_DIR "updown")

    set(GEM5_DEPS m5 rt)

    set(UPDOWNSIMRT_APPS_SRC 
        spmv_coo/spmv_udkvmsr.cpp
        spmv_csr/spmvLBMSRPerfFileTest.cpp
        pr/pagerankMapShuffleReduce.cpp
        tc/tc.cpp
        js/js.cpp
        sorting/sorting.cpp
        gcn_vanilla/gcn_vanilla.cpp
    )

    include_directories(
        common/glib-adv
        common/glib-core
        common/snap-adv
        common/snap-core
        common/snap-exp
        ../libraries/dramalloc
    )

    set(UPDOWNSIMRT_PYTHON_APPS_SRC2BIN
        spmv_coo/spmvMSR.py
        spmv_csr/spmv_msr_exe.py
        spmv_csr/spmv_lbmsr_exe.py
        pr/PagerankMsrEFA.py
        tc/tc_udkvmsr_exe_nlb.py
        tc/tc_udkvmsr_exe_ws.py
        tc/tc_udkvmsr_exe_rh_nlbstrm_off.py
        tc/tc_udkvmsr_exe_rh_nlbstrm_on.py
        tc/tc_udkvmsr_exe_rh_random.py
        js/js_udkvmsr_exe_rh_nlbstrm_off.py
        js/js_udkvmsr_exe_rh_nlbstrm_on.py
        js/js_udkvmsr_exe_rh_random.py
        js/js_udkvmsr_exe_ws.py
        js/js_udkvmsr_exe_nlb.py
        gcn_vanilla/gcn_udkvmsr_exe_rh_nlbstrm_off.py
        gcn_vanilla/gcn_udkvmsr_exe_rh_nlbstrm_on.py
        gcn_vanilla/gcn_udkvmsr_exe_rh_random.py
        gcn_vanilla/gcn_udkvmsr_exe_ws.py
        gcn_vanilla/gcn_udkvmsr_exe_nlb.py
        sorting/sorting_exe.py
    )


    set(UPDOWN_RUNTIME_APPS_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/apps")

    if(UPDOWN_ENABLE_BASIM)
        set(assem_prog "efa2bin.py")
        foreach(PYFILE IN LISTS UPDOWNSIMRT_PYTHON_APPS_SRC2BIN)
            get_filename_component(PYFILEPATH ${PYFILE} REALPATH)
            string(REGEX REPLACE "[.]py$" ".bin" PYBIN ${PYFILE})
            get_filename_component(PYBINFILE ${PYBIN} NAME)
            add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${PYBINFILE}
                               COMMAND ${PYTHON_EXECUTABLE} ${assem_prog}
                               ARGS --efa ${PYFILEPATH} --outpath ${CMAKE_CURRENT_BINARY_DIR} --toplinker
                               WORKING_DIRECTORY ${UPDOWN_ASSEMBLER}
                               DEPENDS ${PYFILEPATH})
            list(APPEND UPDOWNSIMRT_PYTHON_APPS_BIN ${CMAKE_CURRENT_BINARY_DIR}/${PYBINFILE})
        endforeach()
        add_custom_target(apps ALL DEPENDS ${UPDOWNSIMRT_PYTHON_APPS_BIN})
        add_dependencies(apps libraries)
    endif()

    set(DEPS UpDownBASimRuntimeStatic UpDownSimRuntimeStatic m)

    foreach (APPS_SRC ${UPDOWNSIMRT_APPS_SRC})
        get_filename_component(BARENAME ${APPS_SRC} NAME)
        string(REGEX REPLACE "[.]cpp$" "" APPS_NAME ${BARENAME})
        add_executable(${APPS_NAME} ${APPS_SRC} common/snap-core/Snap.o)
        target_link_libraries(${APPS_NAME} ${DEPS} )

        INSTALL(TARGETS ${APPS_NAME}
            RUNTIME DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_PATH}
        )
    endforeach()

    INSTALL(FILES ${UPDOWNSIMRT_PYTHON_APPS_SRC} DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_PATH})
    INSTALL(FILES ${UPDOWNSIMRT_PYTHON_APPS_BIN} DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_PATH})

endif(UPDOWNRT_ENABLE_APPS)
