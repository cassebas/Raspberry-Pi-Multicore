BEGIN {
    print "label,config_series,config_benchmarks,benchmark,cores,pattern,core,cycles,iteration,offset"
}
/CYCLECOUNT/ {
    # Is field number $17 (cycle count) larger than 0? Number of fields must be 21
    if (length($17) > 0 && NF == 21) {
        # remove underscores from benchmark name, it hurts LaTeX
        gsub("_", "", $11)

        # Number of cores $13
        if ($13 == 1) {
            # 1 core
            pattern = "'0'"
        } else if ($13 == 2) {
            # 2 cores
            if ($19 <= 50)
                pattern = "'00'"
            else if ($19 <= 100)
                pattern = "'01'"
            else if ($19 <= 150)
                pattern = "'02'"
            else if ($19 <= 200)
                pattern = "'03'"
            else if ($19 <= 250)
                pattern = "'04'"
            else if ($19 <= 300)
                pattern = "'05'"
            else if ($19 <= 350)
                pattern = "'06'"
            else if ($19 <= 400)
                pattern = "'07'"
            else if ($19 <= 450)
                pattern = "'08'"
            else if ($19 <= 500)
                pattern = "'09'"
        } else if ($13 == 3) {
            # 3 cores
            if ($19 <= 50)
                pattern = "'000'"
            else if ($19 <= 100)
                pattern = "'011'"
            else if ($19 <= 150)
                pattern = "'022'"
            else if ($19 <= 200)
                pattern = "'033'"
            else if ($19 <= 250)
                pattern = "'044'"
            else if ($19 <= 300)
                pattern = "'055'"
            else if ($19 <= 350)
                pattern = "'066'"
            else if ($19 <= 400)
                pattern = "'077'"
            else if ($19 <= 450)
                pattern = "'088'"
            else if ($19 <= 500)
                pattern = "'099'"
        } else {
            # 4 cores
            if ($19 <= 50)
                pattern = "'0000'"
            else if ($19 <= 100)
                pattern = "'0111'"
            else if ($19 <= 150)
                pattern = "'0222'"
            else if ($19 <= 200)
                pattern = "'0333'"
            else if ($19 <= 250)
                pattern = "'0444'"
            else if ($19 <= 300)
                pattern = "'0555'"
            else if ($19 <= 350)
                pattern = "'0666'"
            else if ($19 <= 400)
                pattern = "'0777'"
            else if ($19 <= 450)
                pattern = "'0888'"
            else if ($19 <= 500)
                pattern = "'0999'"
        }

        printf("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",$5,$7,$9,$11,$13,pattern,$15,$17,$19,$21)
    } else {
        printf("WARNING: number of fields doesn't match. Line number is %s\n", NR) | "cat 1>&2"
    }
}
