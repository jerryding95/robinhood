# Distributed Sorting

## Algorithm

1. Redistributed values into buckets
    - We use UDKVMSR, each mapper sends each value to the reducer that is responsible for sorting that value.
    - We assume data distribution is uniform from ```0``` to ```max_value```, where `max_value` is the value that user passes as an argument. We evenly split the range of data across the lanes we are using to sort.
        - Therefore, if the data distribution is not uniform, there might be some buckets that has much more number than the others.
        - If the data distribution is uniform, then each lane will roughly the same number of elements, with some lanes having slightly more than the others.     
2. Local-Sorting per bucket, and deduplication
    - Each lane pull the data in the scratchpad, and do local sort (hybrid quick/insertion sort, by Rajat). 
3. Calculate the final position of each bucket in the final list
    - We run a two-level parallel prefix sum on the sizes of the lists per bucket so that we can know the place of each bucket in the final list.
    - Then we send the buckets into their final positions




See this [document](https://docs.google.com/document/d/1HpXowKyuDWvrsqbNvJPm9mC4rmE_LAQ7yw_wjmK-Pqs/edit) for more information.

## Example
For a more concrete example, refer to ```apps/sorting/sorting.cpp```.

Before using sort:

1. using ```dist_sort = DistributedSort(efa, offset = OFFSET, taskname=taskname, debug_flag=False)``` to initialize distributed sort. 
    -   The sort will use the scratchpad memory from ```OFFSET``` to ```OFFSET + 256 + list_size * 8```, and ```list_size``` is the length of the list one lane gets.
2. use ```dist_sort.generate_sort()``` to generate the sorting program.

Launching sort:

1. Allocate temporary memory for the sorting (and use it as the 4-th argument in the next step). The total temporary memory needed is ```num_input_keys * 100 + num_lanes + (num_lanes + 255) / 256).```
2. send an event to ```{taskname}::distributed_sort``` with the following argument:
	1. No. of elements in the list
	2. DRAM address of the elements
	3. number of lanes, you want to run sorting on.
        - The sort will then use lane ```x``` ~ ```x + num_of_lanes - 1``` to sort the input, where ```x``` is the network ID of the lane that launches the sort.
	4. Temporary DRAM address for the bins & prefix sums
	5. whether to delete duplicates from the list
        - If this option is set to 1, the list will be de-duplicated after being sorted, i.e. the output will only be a sorted list of numbers, where each unique number only appears once.
        - e.g. array [4, 5, 2, 5, 3, 4] will be sorted to [2, 3, 4, 5].
	6. max possible value in the list
3. The sort will return to the continuation word. Operands:
	1. No. of elements in the final list
        - It will decrease to the number of unique values in the original list, if de-duplication is enabled; otherwise, it will stay the same as input.
	2. The DRAM address of the elements
        - This is an in-place sort, so this address will be the same as the input address.
        - suppose `n` = inital_length, `x` = new_length, the first `x` elements will be in the first `x` positions for the original list, and the last `n - x` positions will remain unchanged.
