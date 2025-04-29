class ImplicitFreeListAllocator:
    def __init__(self, size, init_address, word_width):
        self.blocks = [(init_address, size - init_address, 0)]
        self.word_width = word_width
        self.block_break_threshold = 2

    def alloc(self, words):
        if words == 0:
            return 0
        alloc_size = (words + 1) * self.word_width  # Add padding for the header

        target_block = 0
        for i in range(len(self.blocks)):
            _, size, allocated = self.blocks[i]
            if not allocated and size >= alloc_size:
                target_block = i
                break

        addr, size, allocated = self.blocks[target_block]
        remaining = size - alloc_size
        if remaining >= self.block_break_threshold * self.word_width:
            self.blocks.insert(target_block + 1, (addr + alloc_size, remaining, 0))
        else:
            alloc_size = size
        self.blocks[target_block] = (addr, alloc_size, 1)
        return addr + self.word_width

    def free(self, addr):
        successful_free = False
        header_addr = addr - self.word_width
        for i in range(len(self.blocks)):
            if self.blocks[i][0] == header_addr:
                self.blocks[i] = (self.blocks[i][0], self.blocks[i][1], 0)
                successful_free = True
        # Assert that the block was found and freed
        assert successful_free, "Failed free for: {ptr}"

    def playback(self, requests):
        for action, argument in requests:
            if action == "sp_malloc":
                self.alloc(argument)
            elif action == "sp_free":
                self.free(argument)
            else:
                assert False, f"Incorrect action: {action}"
