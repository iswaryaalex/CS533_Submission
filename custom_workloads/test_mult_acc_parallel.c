
 /*
 * The values stored should be able to be loaded by the CPU after the kernel is
 * finished.
 *
 * Performance is dependent on the relationship between the unrolling factor of
 * the inner loop and cache queue size/bandwidth.
 */
#include <stdio.h>
#include <stdlib.h>
#ifndef LLVM_TRACE
#include "aladdin_sys_connection.h"
#include "aladdin_sys_constants.h"
#endif
#define TYPE int
int test_stores(TYPE* store_vals, TYPE* store_loc, TYPE* gold, int num_vals) {
  int num_failures = 0;
  for (int i = 0; i < num_vals; i++) {
    if (store_loc[i] != gold[i] + 2 || store_vals[i] != gold[i] + 2) {
      fprintf(stdout, "FAILED: store_loc[%d] = %d, should be %d\n",
                               i, store_loc[i], store_vals[i] + 2);
      num_failures++;
    }
  }
  return num_failures;
}
char* get_trace_name(int accel_idx) {
  char* buffer = (char*)malloc(30);
  snprintf(buffer, 30, "dynamic_trace_acc%d.gz", accel_idx);
  return buffer;
}
// Read values from store_vals and copy them into store_loc.
void store_kernel(TYPE* store_vals, int num_vals) {
  loop: for (int i = 0; i < num_vals; i++)
    store_vals[i]++;
}
int main() {
  const int num_vals = 32;
  TYPE* store_val =  (TYPE *) malloc (sizeof(TYPE) * num_vals);
  TYPE* store_loc =  (TYPE *) malloc (sizeof(TYPE) * num_vals);
  TYPE* gold =  (TYPE *) malloc (sizeof(TYPE) * num_vals);
  TYPE* store_vals;
  for (int i = 0; i < num_vals; i++) {
    store_val[i] = i;
    store_loc[i] = i;
    gold[i] = i;
  }
  volatile int* flag[2];
  for (int acc = 0; acc < 2; acc++) {
        if (acc == 0)
                store_vals = store_val;
        else
                store_vals = store_loc;
#ifdef LLVM_TRACE
        llvmtracer_set_trace_name(get_trace_name(acc));
        store_kernel(store_vals, num_vals);
#else
        mapArrayToAccelerator(
                INTEGRATION_TEST + acc, "store_vals", &(store_vals[0]), num_vals * sizeof(int));
        fprintf(stdout, "Invoking accelerator!\n");
        flag[acc] = invokeAcceleratorAndReturn(INTEGRATION_TEST + acc);
        fprintf(stdout, "Accelerator finished!\n");
        if (acc == 1) {
                for (int i = 0; i < 2; i ++) {
                        waitForAccelerator(flag[i]);
                        free((void*)flag[i]);
                }
        }
#endif
  }
  for (int acc = 0; acc < 2; acc++) {
        if (acc == 1)
                store_vals = store_val;
        else
                store_vals = store_loc;
#ifdef LLVM_TRACE
        llvmtracer_set_trace_name(get_trace_name(acc));
        store_kernel(store_vals, num_vals);
#else
        mapArrayToAccelerator(
                INTEGRATION_TEST + acc, "store_vals", &(store_vals[0]), num_vals * sizeof(int));
        fprintf(stdout, "Invoking accelerator!\n");
        flag[acc] = invokeAcceleratorAndReturn(INTEGRATION_TEST + acc);
        fprintf(stdout, "Accelerator finished!\n");
        if (acc == 1) {
                for (int i = 0; i < 2; i ++) {
                        waitForAccelerator(flag[i]);
                        free((void*)flag[i]);
                }
        }
#endif
  }
  int num_failures = test_stores(store_val, store_loc, gold, num_vals);
  if (num_failures != 0) {
    fprintf(stdout, "Test failed with %d errors.", num_failures);
    return -1;
  }
  fprintf(stdout, "Test passed!\n");
  return 0;
}
