#ifndef __spmalloc_test_exe_H__
#define __spmalloc_test_exe_H__

namespace spmalloc_test_exe {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol lm_allocator__spmalloc = 0;
    constexpr EventSymbol lm_allocator__spfree = 1;
    constexpr EventSymbol start_event = 2;
    constexpr EventSymbol write_crap = 3;
    constexpr EventSymbol terminate_event = 4;

} // namespace

#endif