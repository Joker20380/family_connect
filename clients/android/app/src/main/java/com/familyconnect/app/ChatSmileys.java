package com.familyconnect.app;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Local rendering only: original text is signed, stored and transmitted unchanged. */
final class ChatSmileys {
    static final class Face {
        final String token,label;
        Face(String token,String label){this.token=token;this.label=label;}
    }
    static final List<Face> FACES=Collections.unmodifiableList(java.util.Arrays.asList(
        new Face(":)","Улыбка"),new Face(";)","Подмигивание"),new Face(":D","Смех"),
        new Face(":(","Грусть"),new Face(":-P","Язык"),new Face("=-O","Удивление"),
        new Face(":'(","Слёзы"),new Face("8-)","Крутой")));
    static final class Match {
        final int start,end,index;
        Match(int start,int end,int index){this.start=start;this.end=end;this.index=index;}
    }
    static List<Match> find(String text) {
        if(text.length()>4096)throw new IllegalArgumentException("Chat text too long");
        List<Match> matches=new ArrayList<>();
        for(int i=0;i<text.length();i++) {
            if(i>0&&!Character.isWhitespace(text.charAt(i-1)))continue;
            for(int j=0;j<FACES.size();j++) {
                String token=FACES.get(j).token;int end=i+token.length();
                if(text.startsWith(token,i)&&(end==text.length()||Character.isWhitespace(text.charAt(end)))) {
                    matches.add(new Match(i,end,j));i=end-1;break;
                }
            }
        }
        return matches;
    }
}
