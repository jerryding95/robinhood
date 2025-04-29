import argparse

from heap_simulator import ImplicitFreeListAllocator

def read_block_logs(log_fname):
    with open(log_fname) as f:
        data = f.readlines()
    heap_logs = []
    for line in data:
        output, blocks = [e.strip() for e in line.split("-->")]
        address, success = [int(e.strip()) for e in output[6:-1].split(",")]

        blocks = [tuple([int(e.strip()) for e in b[1:-1].split(",")]) for b in blocks.split(";")]
        heap_logs.append((address, success, blocks))
    return heap_logs

def read_action_logs(actions_fname):
    with open(actions_fname) as f:
        data = f.readlines()
    action_logs = []
    for line in data:
        action, argument = line.split(",")
        action_logs.append((action, int(argument)))
    return action_logs

def validate(heap, heap_logs, action_logs):
    for idx, (action, (addr, _, blocks)) in enumerate(zip(action_logs, heap_logs)):
        func_call, argument = action
        if func_call == "sp_malloc":
            assert addr == heap.alloc(argument)
        assert heap.blocks == blocks, f"Invalid blocks on call {idx} {func_call}({argument}):\n{heap.blocks}\n{blocks}"

def main(args):
    heap_logs = read_block_logs(args.log_file)
    action_logs = read_action_logs(args.action_file)

    if args.heap_type == "ImplicitFreeList":
        heap = ImplicitFreeListAllocator(args.size, args.init_address, args.word_width)
    else:
        print(f"Invalid allocator {args.heap_type}")
        exit(1)

    validate(heap, heap_logs, action_logs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="heap_validator")

    # Arguments for Heap simulator
    parser.add_argument("--heap", dest="heap_type", required=True, choices=["ImplicitFreeList"], type=str)
    parser.add_argument("--init_address", dest="init_address", required=True, type=int)
    parser.add_argument("--word_width", dest="word_width", default=4, type=int)
    parser.add_argument("--size", dest="size", default=64 * 1024, type=int)

    # Arguments for validation
    parser.add_argument("--log_file", dest="log_file", required=True, type=str)
    parser.add_argument("--action_file", dest="action_file", required=True, type=str)

    args = parser.parse_args()

    main(args)
