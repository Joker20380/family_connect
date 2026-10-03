package com.familyconnect.app;

final class SupportId {
    static boolean valid(String value){return value!=null&&value.matches("FC-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}");}
    static String require(String value){if(!valid(value))throw new IllegalArgumentException("Support ID");return value;}
}
