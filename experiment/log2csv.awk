BEGIN {
    print "configuration,benchmark,dassign,cores,pattern,core,cycles,iteration,offset"
}
{
    if (length($15) > 0 && NF == 19) {
        # remove underscores from benchmark name, it hurts LaTeX
        gsub("_", "", $6)

        if ($10 == 1) {
            /* 1 core */
            printf("%s,%s,%s,%s,'0',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
         } else if ($10 == 2) {
            /* 2 cores */
            if ($17 <= 2000)
                printf("%s,%s,%s,%s,'00',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
            else if ($17 <= 4000)
                printf("%s,%s,%s,%s,'01',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
            else if ($17 <= 6000)
                printf("%s,%s,%s,%s,'02',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
        } else if ($10 == 3) {
            /* 3 cores */
            if ($17 <= 2000)
                printf("%s,%s,%s,%s,'000',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
            else if ($17 <= 4000)
                printf("%s,%s,%s,%s,'011',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
            else if ($17 <= 6000)
                printf("%s,%s,%s,%s,'022',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
        } else {
            /* 4 cores */
            if ($17 <= 2000)
                printf("%s,%s,%s,%s,'0000',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
            else if ($17 <= 4000)
                printf("%s,%s,%s,%s,'0111',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
            else if ($17 <= 6000)
                printf("%s,%s,%s,%s,'0222',%s,%s,%s,%s\n",$4,$6,$8,$10,$12,$15,$17,$19)
        }
   }
}
