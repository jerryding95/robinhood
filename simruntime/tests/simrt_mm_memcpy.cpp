#include <iostream>
#include <simupdown.h>

#define N 15

int main() {
  // Default configurations runtime
  UpDown::SimUDRuntime_t *test_rt = new UpDown::SimUDRuntime_t();

  printf("=== Base Addresses ===\n");
  test_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  test_rt->dumpMachineConfig();

  UpDown::word_t anArray[N];
  UpDown::word_t anArray2[N];

  for (int i = 0; i < N; i++)
    anArray[i] = i;

  // 1 element at a time
  printf("\nCopying from top to updown\n");
  for (int i = 0; i < N; i++)
    test_rt->t2mm_memcpy(i, anArray + i, sizeof(UpDown::word_t));

  printf("\nCopying from updown to top\n");
  for (int i = 0; i < N; i++)
    test_rt->mm2t_memcpy(i,anArray2 + i, sizeof(UpDown::word_t));

  for (int i = 0; i < N; i++)
    printf("AnArray2[%d] = %d\n", i, anArray2[i]);

  // Change values of array
  for (int i = 0; i < N; i++)
    anArray[i] = -i;

  printf("\nCopying from top to updown\n");
  test_rt->t2mm_memcpy(N,anArray, N*sizeof(UpDown::word_t));
  printf("\nCopying from updown to top\n");
  test_rt->mm2t_memcpy(N,anArray2, N*sizeof(UpDown::word_t));

  for (int i = 0; i < N; i++)
    printf("AnArray2[%d] = %d\n", i, anArray2[i]);

  delete test_rt;
  return 0;
}