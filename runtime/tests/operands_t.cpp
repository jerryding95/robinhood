#include <iostream>
#include <updown.h>

int main() {
  // Create an empty operands_t
  UpDown::operands_t empty_ops;
  printf("Empty operands_t NumOperands = %d, Data = 0x%lX\n",
         empty_ops.get_NumOperands(), (uint64_t)empty_ops.get_Data());

  // Create an operand_t with operands
  UpDown::word_t ops_data[] = {1, 2, 3, 4};
  UpDown::operands_t set_ops(4, ops_data);
  printf("NumOperands = %d, Data = ", set_ops.get_NumOperands());
  for (uint8_t i = 0; i < set_ops.get_NumOperands() + 1; i++)
    printf("%lu ", set_ops.get_Data()[i]);
  printf("\n");

  // Create an event with a continuation
  UpDown::operands_t set_ops_cont(4, ops_data, 99);
  printf("NumOperands = %d, Data = ", set_ops_cont.get_NumOperands());
  for (uint8_t i = 0; i < set_ops_cont.get_NumOperands() + 1; i++)
    printf("%lu ", set_ops_cont.get_Data()[i]);
  printf("\n");
  return 0;
}