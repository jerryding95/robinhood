if (UPDOWNRT_ENABLE_TESTS)

    set(UPDOWNRT_TESTS_SRC 
        operands_t.cpp
        event_t.cpp 
        rt_calc_addrmap.cpp 
        rt_mm_malloc_free.cpp
    )

        set(UPDOWN_RUNTIME_TESTS_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/tests")

        foreach (TEST_SRC ${UPDOWNRT_TESTS_SRC})
            string(REGEX REPLACE "[.]cpp$" "" TEST_NAME ${TEST_SRC})
            add_executable(${TEST_NAME} ${TEST_SRC})
            target_link_libraries(${TEST_NAME} UpDownRuntime)

            INSTALL(TARGETS ${TEST_NAME}
                RUNTIME DESTINATION ${UPDOWN_RUNTIME_TESTS_INSTALL_PATH}
            )
        endforeach()



endif(UPDOWNRT_ENABLE_TESTS)