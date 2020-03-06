BEGIN{
    print("#ifndef RANDOM_SETS_H")
    print("#define RANDOM_SETS_H")
    print
    print("#include <stdint.h>")
    print
    print("#define MAX_SETS 200")
    print
    print("uint16_t random_set[MAX_SETS][MAX_SYNBENCH_DATASIZE] = {")
}
{
    /* if reading first row, don't end previous row with a comma */
    if (NR == 1)
        printf("\t {")
    else
        printf(",\n\t {")

    /* just print all the numbers from the 3rd field until the end */
    for (i=3; i<=NF; i++)
        printf($i)

    /* end each row with a bracket */
    printf("}")
}
END {
    printf("\n};\n\n")
    print("#endif /* RANDOM_SETS_H */")
}
