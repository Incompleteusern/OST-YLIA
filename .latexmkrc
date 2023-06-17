sub asy {return system("asy \"$_[0]\"");}
add_cus_dep("asy","eps",0,"asy");
add_cus_dep("asy","pdf",0,"asy");
add_cus_dep("asy","tex",0,"asy");

sub pythontex {
    system("pythontex --runall true \"$_[0]\"");
    system("touch \$(basename \"$_[0]\").pytxmcr");
    return;
}
add_cus_dep("pytxcode", "pytxmcr", 0, "pythontex");