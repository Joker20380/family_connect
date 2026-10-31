package com.familyconnect.app;

import java.util.Locale;

final class ServerLoadPresentation {
    final Double percent;
    final String title,value,details;

    private ServerLoadPresentation(Double percent,String title,String value,String details){
        this.percent=percent;this.title=title;this.value=value;this.details=details;
    }

    static ServerLoadPresentation from(ServerLoad sample,String country,double now,boolean ru){
        if(sample==null||!sample.country.equals(country)||!sample.fresh(now)){
            String missing=ru?"Нет данных":"No data";
            return new ServerLoadPresentation(null,ru?"Нагрузка сервера":"Server load",missing,missing);
        }
        boolean cpuOnly=sample.percent==null;
        double percent=cpuOnly?sample.cpu:sample.percent;
        String title=cpuOnly?(ru?"CPU сервера":"Server CPU"):(ru?"Нагрузка сервера":"Server load");
        String value=(cpuOnly?"CPU ":sample.estimated?"≈ ":"")+Math.round(percent)+"%";
        String details=String.format(Locale.ROOT,"CPU %.0f%% · ↓ %.1f / ↑ %.1f Mbps",sample.cpu,sample.rx,sample.tx);
        if(cpuOnly)details+=ru?" · загрузка канала неизвестна":" · channel utilization unknown";
        else if(sample.estimated)details+=ru?" · оценка загрузки канала":" · estimated channel utilization";
        return new ServerLoadPresentation(percent,title,value,details);
    }

    String label(){return title+" · "+(value.startsWith("CPU ")?value.substring(4):value);}
}
