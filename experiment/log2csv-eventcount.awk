BEGIN {
    print "label,config_series,config_benchmarks,cores,pattern,core,pmu,eventtype,eventcount,iteration"
}
/EVENTCOUNT/ {
    # Number of fields must be 21
    if (NF == 21) {
        # Number of cores $11
        if ($11 == 1) {
            # 1 core
            pattern = "'0'"
        } else if ($11 == 2) {
            # 2 cores
            if ($21 <= 100)
                pattern = "'00'"
            else if ($21 <= 200)
                pattern = "'01'"
            else if ($21 <= 300)
                pattern = "'02'"
            else if ($21 <= 400)
                pattern = "'03'"
        } else if ($11 == 3) {
            # 3 cores
            if ($21 <= 100)
                pattern = "'000'"
            else if ($21 <= 200)
                pattern = "'012'"
            else if ($21 <= 300)
                pattern = "'024'"
            else if ($21 <= 400)
                pattern = "'036'"
        } else {
            # 4 cores
            if ($21 <= 100)
                pattern = "'0000'"
            else if ($21 <= 200)
                pattern = "'0123'"
            else if ($21 <= 300)
                pattern = "'0246'"
            else if ($21 <= 400)
                pattern = "'0369'"
        }
        printf("%s,%s,%s,%s,%s,%s,%s,%s,%s\n",$5,$7,$9,$11,pattern,$13,$15,$17,$19,$21)
    } else {
        printf("WARNING: number of fields doesn't match. Line number is %s\n", NR) | "cat 1>&2"
    }
}
