# SpMalloc


## High Level Design

SpMalloc is a library for managing the scratchpad space on the UpDown accelerator. It uses an implicit free list to keep track of the available space.
Every allocated block starts with a 1-word value indicating the size of the block and whether it is free. The library is responsible for creating, 
releasing, and coalescing of these blocks.


## Usage

SpMalloc allows the user to reserve a segment at the start of the scratchpad which the library will not use. This is done by setting designated location in the scratchpad.
The location of the offset value is set by users when they initialize the library. For example, if the segment after offset 1600 is available, then init_offset should be 
to 1600. Then for address X7 + 1600, we need to write 1608 so that the library does not accidently overwrite the offset.


## APIs


#### `Allocating Space`

``` c

    (uint64_t* address, uint64_t status) 
    spmalloc(
        uint64_t size
        );
```

- Allocate size words on the scratchpad

- Operands
    1. `X8`  - `size` - size of the requested space (in words)

- Returns
    1. `X8` - `address` - scratchpad address being allocated (0 if allocation failed)
    2. `X9` - `status` - status of the allocation (1 for success and 0 for failure)


#### `Freeing Space`

``` c

    (uint64_t status) 
    spfree(
        uint64_t* target_address
        );
```

- Free the allocated space once the user is done using it.

- Operands
    1. `X8`  - `target_address` - pointer to the start of an allocated scratchpad region.

- Returns
    1. `X8` - ``status`` - status of free 1 for success, 0 for failure

