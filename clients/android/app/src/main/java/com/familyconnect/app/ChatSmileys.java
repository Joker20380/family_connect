package com.familyconnect.app;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Local rendering only: original text is signed, stored and transmitted unchanged. */
final class ChatSmileys {
    static final class Face {
        final String token,label,asset;
        final List<String> aliases;
        Face(String token,String label,String asset,String... aliases){
            this.token=token;this.label=label;this.asset=asset;
            this.aliases=Collections.unmodifiableList(java.util.Arrays.asList(aliases));
        }
    }
    static final List<Face> FACES=Collections.unmodifiableList(java.util.Arrays.asList(
        new Face("O=)","Ангел","aa.gif","O=)","O:-)"),
        new Face(":)","Улыбка","ab.gif",":)","=)",":-)"),
        new Face(":(","Грусть","ac.gif",":(",";(",":-("),
        new Face(";)","Подмигивание","ad.gif",";)",";-)"),
        new Face(":P","Язык","ae.gif",":P",":-P"),
        new Face("8-)","Очки","af.gif","8-)"),
        new Face(":D","Смех","ag.gif",":D",":-D"),
        new Face(":-[","Смущение","ah.gif",":-["),
        new Face("=-O","Удивление","ai.gif","=-O"),
        new Face(":-*","Поцелуй","aj.gif",":-*"),
        new Face(":'(","Плач","ak.gif",":'("),
        new Face(":-X","Молчу","al.gif",":-X",":-x"),
        new Face(">:o","Крик","am.gif",">:o"),
        new Face(":-|","Безразличие","an.gif",":-|"),
        new Face(":-/","Недовольство","ao.gif",":-/",":-\\"),
        new Face("*JOKINGLY*","Шутка","ap.gif","*JOKINGLY*"),
        new Face("]:->","Дьявол","aq.gif","]:->"),
        new Face("[:-}","Диджей","ar.gif","[:-}"),
        new Face("*KISSED*","Зацелован","as.gif","*KISSED*"),
        new Face(":-!","Тошнит","at.gif",":-!"),
        new Face("*TIRED*","Устал","au.gif","*TIRED*"),
        new Face("*STOP*","Стоп","av.gif","*STOP*"),
        new Face("*KISSING*","Целую","aw.gif","*KISSING*"),
        new Face("@}->--","Роза","ax.gif","@}->--"),
        new Face("*THUMBS UP*","Класс","ay.gif","*THUMBS UP*"),
        new Face("*DRINK*","Выпьем","az.gif","*DRINK*"),
        new Face("*IN LOVE*","Влюблён","ba.gif","*IN LOVE*"),
        new Face("@=","Бомба","bb.gif","@="),
        new Face("*HELP*","Помогите","bc.gif","*HELP*"),
        new Face("\\m/","Рок","bd.gif","\\m/"),
        new Face("%)","Безумие","be.gif","%)"),
        new Face("*OK*","Окей","bf.gif","*OK*"),
        new Face("*SUP*","Как дела","bg.gif","*SUP*","*WASSUP*"),
        new Face("*SORRY*","Извини","bh.gif","*SORRY*"),
        new Face("*BRAVO*","Браво","bi.gif","*BRAVO*"),
        new Face("*LOL*","Катаюсь от смеха","bj.gif","*LOL*","*ROFL*"),
        new Face("*PARDON*","Прошу прощения","bk.gif","*PARDON*"),
        new Face("*NO*","Нет","bl.gif","*NO*"),
        new Face("*CRAZY*","Сумасшедший","bm.gif","*CRAZY*"),
        new Face("*UNKNOWN*","Не знаю","bn.gif","*UNKNOWN*","*DONT_KNOW*"),
        new Face("*DANCE*","Танец","bo.gif","*DANCE*"),
        new Face("*YAHOO*","Ура","bp.gif","*YAHOO*","*YAHOO!*"),
        new Face("*HI*","Привет","bq.gif","*HI*","*HELLO*","*PREVED*","*PRIVET*"),
        new Face("*BYE*","Пока","br.gif","*BYE*"),
        new Face("*YES*","Да","bs.gif","*YES*"),
        new Face(";D","Хитрый","bt.gif",";D","*ACUTE*"),
        new Face("*DASH*","Об стену","bu.gif","*DASH*","*WALL*"),
        new Face("*MAIL*","Пишу","bv.gif","*MAIL*","*WRITE*"),
        new Face("*SCRATCH*","Чешу затылок","bw.gif","*SCRATCH*")));
    static final class Match {
        final int start,end,index;
        Match(int start,int end,int index){this.start=start;this.end=end;this.index=index;}
    }
    static List<Match> find(String text) {
        if(text.length()>4096)throw new IllegalArgumentException("Chat text too long");
        List<Match> matches=new ArrayList<>();
        for(int i=0;i<text.length();i++) {
            if(i>0&&!Character.isWhitespace(text.charAt(i-1)))continue;
            Match best=null;
            for(int j=0;j<FACES.size();j++) {
                for(String token:FACES.get(j).aliases) {
                    int end=i+token.length();
                    if(text.startsWith(token,i)&&(end==text.length()||Character.isWhitespace(text.charAt(end)))
                            &&(best==null||end>best.end))best=new Match(i,end,j);
                }
            }
            if(best!=null){matches.add(best);i=best.end-1;}

        }
        return matches;
    }
}
