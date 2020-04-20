BEGIN {
    print "label,configuration,benchmark,dassign,cores,pattern,core,cycles,iteration,offset"
}
{
    if (length($16) > 0 && NF == 20) {
        # remove underscores from benchmark name, it hurts LaTeX
        gsub("_", "", $7)

        if ($11 == 1) {
            /* 1 core */
            printf("%s,%s,%s,%s,%s,'0',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
         } else if ($11 == 2) {
            /* 2 cores */
            if ($18 <= 2000)
                printf("%s,%s,%s,%s,%s,'00',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
            else if ($18 <= 4000)
                printf("%s,%s,%s,%s,%s,'01',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
            else if ($18 <= 6000)
                printf("%s,%s,%s,%s,%s,'02',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
        } else if ($11 == 3) {
            /* 3 cores */
            if ($18 <= 2000)
                printf("%s,%s,%s,%s,%s,'000',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
            else if ($18 <= 4000)
                printf("%s,%s,%s,%s,%s,'011',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
            else if ($18 <= 6000)
                printf("%s,%s,%s,%s,%s,'022',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
        } else {
            /* 4 cores */
            if ($18 <= 2000)
                printf("%s,%s,%s,%s,%s,'0000',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
            else if ($18 <= 4000)
                printf("%s,%s,%s,%s,%s,'0111',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
            else if ($18 <= 6000)
                printf("%s,%s,%s,%s,%s,'0222',%s,%s,%s,%s\n",$3,$5,$7,$9,$11,$13,$16,$18,$20)
        }
    } else {
        print(NF)
    }
}
