BEGIN {
    print "benchmark,cores,pattern,core,cycles,iteration,offset"
}
{
    if (length($15) > 0) {
        # remove underscores from benchmark name, it hurts LaTeX
        gsub("_", "", $4)

        if ($6 == 1) {
            /* 1 core */
            if ($15 <= 2000)
                printf("%s,%s,'0',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
            else if ($15 <= 4000)
                printf("%s,%s,'0',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
            else if ($15 <= 6000)
                printf("%s,%s,'0',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
         } else if ($6 == 2) {
            /* 2 cores */
            if ($15 <= 2000)
                printf("%s,%s,'00',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
            else if ($15 <= 4000)
                printf("%s,%s,'01',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
            else if ($15 <= 6000)
                printf("%s,%s,'02',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
        } else if ($6 == 3) {
            /* 3 cores */
            if ($15 <= 2000)
                printf("%s,%s,'000',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
            else if ($15 <= 4000)
                printf("%s,%s,'011',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
            else if ($15 <= 6000)
                printf("%s,%s,'022',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
        } else {
            /* 4 cores */
            if ($15 <= 2000)
                printf("%s,%s,'0000',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
            else if ($15 <= 4000)
                printf("%s,%s,'0111',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
            else if ($15 <= 6000)
                printf("%s,%s,'0222',%s,%s,%s,%s\n",$4,$6,$8,$13,$15,$17)
        }
   }
}
