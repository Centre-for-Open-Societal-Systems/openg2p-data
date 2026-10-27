# Audit Log: Seed Variety Quality Transformations & Deduplication

## 1. Verified Official Citations for Resolved Pairs

- **Deka (ETBW 6583)**: Released in 2018 by Kulumsa Agricultural Research Center (KARC / EIAR). Source: Ministry of Agriculture (MoA) Ethiopia, *Plant Variety Release, Protection and Seed Quality Control Directorate - Crop Variety Register*, Issue No. 21 (June 2018), Bread Wheat (*Triticum aestivum L.*).
- **Awash-1**: 1990 release by Melkassa Agricultural Research Center (MARC / EIAR), officially registered white pea bean (*Phaseolus vulgaris L.*) in MoA Crop Variety Register.
- **Awash Mitra**: 2017 release by Melkassa ARC / EIAR, canning/navy bean variety officially registered in MoA Crop Variety Register Issue No. 20 (June 2017).

## 2. Decision on Maize Breeding Parent Lines

In accordance with the OpenG2P MDS / Agri-Stack data standards, `SEED_VARIETY` represents farmer-plantable cultivars. Parental inbred and single-cross lines (e.g., `142-1-e`, `A7033/F-7215`, `CML395`, `BKL001-BKL004`, `SC22`, `124-b(109)`) are used exclusively by certified seed producers for hybrid multiplication. These 14 entries (rows 776, 793..804, 897) have been omitted from `SEED_VARIETY` and reserved for producer catalogs.

## 3. Shortened Varieties (from ellipsis truncation in archived source)

| Row ID | Source Name | Resulting Code | Resulting Display |
|---|---|---|---|
| 4 | `Tef - Bishoftu (ቢሾፍቱ ) …` | `VAR_TEFF_BISHOFTU` | Tef – Bishoftu |
| 21 | `Food Barley - Jalqabne (BARC/JED/003/14) …` | `VAR_BARLEY_JALQABNE` | Food Barley – Jalqabne (BARC/JED/003/14) |
| 23 | `Malt Barley - Suba (Pedigree: …` | `VAR_MALT_BARLEY_SUBA` | Malt Barley – Suba |
| 26 | `Fiel pea - Kuullee (EH08027-2) …` | `VAR_FIELD_PEA_KUULLEE` | Field pea – Kuullee (EH08027-2) |
| 27 | `Field pea - Jirraafi (EH05011-2) …` | `VAR_FIELD_PEA_JIRRAAFI` | Field pea – Jirraafi (EH05011-2) |
| 28 | `Field pea - Hasset (ሀሴት) …` | `VAR_FIELD_PEA_HASSET` | Field pea – Hasset |
| 29 | `Field pea - Mieso (ሜኤሶ) …` | `VAR_FIELD_PEA_MIESO` | Field pea – Mieso |
| 30 | `Fiel pea - Etetu (እቴቱ) …` | `VAR_FIELD_PEA_ETETU` | Field pea – Etetu |
| 31 | `Chickpea - (Girar) ግራር ICCMABCA …` | `VAR_CHICKPEA_GIRAR` | Chickpea – Girar (ICCMABCA) |
| 49 | `Sesame - Hachalu (EW006 x …` | `VAR_SESAME_HACHALU` | Sesame – Hachalu |
| 60 | `Sweet/Hot Pepper - Oda Gibe …` | `VAR_PEPPER_ODA_GIBE` | Sweet/Hot Pepper – Oda Gibe |
| 81 | `Bread wheat - Adola 1 …` | `VAR_BREAD_WHEAT_ADOLA_1` | Bread Wheat – Adola 1 |
| 83 | `Bread Wheat - Netsanet (ነፃነት) …` | `VAR_BREAD_WHEAT_NETSANET` | Bread Wheat – Netsanet |
| 86 | `Bread Wheat - Adet-1 (BAJ …` | `VAR_BREAD_WHEAT_ADET_1` | Bread Wheat – Adet-1 |
| 87 | `Brachiaria brizantha cv.Xaraes - Xaraes …` | `VAR_BRACHIARIA_XARAES` | Brachiaria – Xaraes |
| 93 | `Tef - Washera (353*Key muri) …` | `VAR_TEFF_WASHERA` | Tef – Washera (353*Key muri) |
| 95 | `Tef - Mena (DZ-01-354 X …` | `VAR_TEFF_MENA` | Tef – Mena |
| 96 | `Tef - Ebba (Kay muri …` | `VAR_TEFF_EBBA` | Tef – Ebba |
| 97 | `Bread Wheat - Korem 1 …` | `VAR_BREAD_WHEAT_KOREM_1` | Bread Wheat – Korem 1 |
| 98 | `Bread Wheat - Ardi (GLADIUS/2*BAVIS) …` | `VAR_BREAD_WHEAT_ARDI` | Bread Wheat – Ardi (GLADIUS/2*BAVIS) |
| 99 | `Bread Wheat - Ga’ambo-2 (HEILO/MILAN/MUNIA/3/KIRITATI/2*TRCH) …` | `VAR_BREAD_WHEAT_GA_AMBO_2` | Bread Wheat – Ga’ambo-2 (HEILO/MILAN/MUNIA/3/KIRITATI/2*TRCH) |
| 101 | `Bread Wheat - Balcha (ETB …` | `VAR_BREAD_WHEAT_BALCHA` | Bread Wheat – Balcha |
| 102 | `Bread Wheat - Galan (ETBW8003 …` | `VAR_BREAD_WHEAT_GALAN` | Bread Wheat – Galan |
| 103 | `Triticale - Kombolcha (Acc. 2012 …` | `VAR_TRITICALE_KOMBOLCHA` | Triticale – Kombolcha |
| 108 | `Maize - CP.201 (IQT5024 X …` | `VAR_MAIZE_CP_201` | Maize – CP.201 |
| 109 | `Maize - CP.838 (SKQPP422 X …` | `VAR_MAIZE_CP_838` | Maize – CP.838 |
| 110 | `Sorghum - ጥላሁን (Tilahun) 14MWLSDT7114 …` | `VAR_SORGHUM_TILAHUN` | Sorghum – Tilahun (14MWLSDT7114) |
| 116 | `Sorghum - Fadis 01 (M-36121 …` | `VAR_SORGHUM_FADIS_01` | Sorghum – Fadis 01 |
| 117 | `Finger Millet - : Kumsa …` | `VAR_FINGER_MILLET_KUMSA` | Finger Millet – Kumsa |
| 118 | `Finger Millet - Jabi (ጃቢ) …` | `VAR_FINGER_MILLET_JABI` | Finger Millet – Jabi |
| 120 | `Malt Barley - Henrike (Pedigree: …` | `VAR_MALT_BARLEY_HENRIKE` | Malt Barley – Henrike |
| 121 | `Malt Barley - Waro (LIBRA …` | `VAR_MALT_BARLEY_WARO` | Malt Barley – Waro |
| 124 | `Faba bean - Moybon (ሞይቦን) …` | `VAR_FABA_BEAN_MOYBON` | Faba bean – Moybon |
| 125 | `Faba bean - Tosha (ቶሻ) …` | `VAR_FABA_BEAN_TOSHA` | Faba bean – Tosha |
| 126 | `Field pea - Jeldu (ጀልዱ) …` | `VAR_FIELD_PEA_JELDU` | Field pea – Jeldu |
| 135 | `Sorghum - Marara [ETSL 101371 …` | `VAR_SORGHUM_MARARA` | Sorghum – Marara |
| 143 | `Sesame - Yale ( EW002 …` | `VAR_SESAME_YALE` | Sesame – Yale |
| 145 | `Sesame - Hagalo ( EW002 …` | `VAR_SESAME_HAGALO` | Sesame – Hagalo |
| 149 | `Finger Millet - Metekili (Acc. …` | `VAR_FINGER_MILLET_METEKILI` | Finger Millet – Metekili |
| 150 | `Groundnut - ድርብ /Direb (ICGV-97164 …` | `VAR_GROUNDNUT_DIREB` | Groundnut – Direb |
| 152 | `Food barley - Negele (LMON …` | `VAR_BARLEY_NEGELE` | Food Barley – Negele |
| 153 | `Malt barley - Iftuu (Mn …` | `VAR_MALT_BARLEY_IFTUU` | Malt Barley – Iftuu |
| 169 | `Tef - Areka-1 (Dz-01-974 X …` | `VAR_TEFF_AREKA_1` | Tef – Areka-1 |
| 173 | `Bread Wheat - JAALANNE (ETBW …` | `VAR_BREAD_WHEAT_JAALANNE` | Bread Wheat – JAALANNE |
| 174 | `Bread Wheat - JAJABO (ETB …` | `VAR_BREAD_WHEAT_JAJABO` | Bread Wheat – JAJABO |
| 175 | `Bread Wheat - Fentale – …` | `VAR_BREAD_WHEAT_FENTALE` | Bread Wheat – Fentale |
| 176 | `Bread Wheat - Amibara – …` | `VAR_BREAD_WHEAT_AMIBARA` | Bread Wheat – Amibara |
| 177 | `Durem Wheat - Bullaallaa (Durum …` | `VAR_DURUM_WHEAT_BULLAALLAA` | Durum Wheat – Bullaallaa |
| 178 | `Durem Wheat - Alemtena (43IDSNMeh …` | `VAR_DURUM_WHEAT_ALEMTENA` | Durum Wheat – Alemtena |
| 179 | `Durem Wheat - Tesfaye (43IDSNMeh …` | `VAR_DURUM_WHEAT_TESFAYE` | Durum Wheat – Tesfaye |
| 187 | `Bread wheat - Hadis (ETBW …` | `VAR_BREAD_WHEAT_HADIS` | Bread Wheat – Hadis |
| 192 | `Bread Wheat - Bondena (ETBW …` | `VAR_BREAD_WHEAT_BONDENA` | Bread Wheat – Bondena |
| 195 | `Bread Wheat - Deka (ETBW …` | `VAR_BREAD_WHEAT_DEKA` | Bread Wheat – Deka |
| 196 | `Maize - Afran Qalloo (HrU …` | `VAR_MAIZE_AFRAN_QALLOO` | Maize – Afran Qalloo |
| 200 | `Bread Wheat - Hibist (ETBW …` | `VAR_BREAD_WHEAT_HIBIST` | Bread Wheat – Hibist |
| 203 | `Bread Wheat- Sinja (Dure/Madda Walabu …` | `VAR_BREAD_WHEAT_SINJA` | Bread Wheat – Sinja |
| 206 | `Sorghum - አርጊቲ (2005M15064) (WSV387 …` | `VAR_SORGHUM_ARGITI` | Sorghum – Argiti (2005M15064) |
| 207 | `Sorghum - Alene (WSV-387 x …` | `VAR_SORGHUM_ALENE` | Sorghum – Alene |
| 209 | `Food Barley - DEBARK-1 (Acc …` | `VAR_BARLEY_DEBARK_1` | Food Barley – DEBARK-1 |
| 215 | `Faba Bean - Alloshe (አሎሼ) …` | `VAR_FABA_BEAN_ALLOSHE` | Faba bean – Alloshe |
| 219 | `Field Pea - Yewaginesh (የዋግነሽ) …` | `VAR_FIELD_PEA_YEWAGINESH` | Field pea – Yewaginesh |
| 220 | `Field Pea - Hortu (ሆርቱ) …` | `VAR_FIELD_PEA_HORTU` | Field pea – Hortu |
| 221 | `Field Pea - Weyib (ዌይብ) …` | `VAR_FIELD_PEA_WEYIB` | Field pea – Weyib |
| 227 | `Common Bean/Haricot bean - Awash …` | `VAR_COMMON_BEAN_AWASH_MITRA` | Common/Haricot/ bean – Awash Mitra |
| 239 | `Food barley - Hagere (Feres …` | `VAR_BARLEY_HAGERE` | Food Barley – Hagere |
| 241 | `Tef - Abola (7 (Quncho …` | `VAR_TEFF_ABOLA` | Tef – Abola |
| 248 | `Bread Wheat - Amibera (DOUKKALA-4 …` | `VAR_BREAD_WHEAT_AMIBERA` | Bread Wheat – Amibera |
| 251 | `Bread Wheat - Bulluq (ETBW …` | `VAR_BREAD_WHEAT_BULLUQ` | Bread Wheat – Bulluq |
| 252 | `Bread Wheat - Liben (ETBW …` | `VAR_BREAD_WHEAT_LIBEN` | Bread Wheat – Liben |
| 256 | `Maize - SPRH1 Hybrid (CUBA/GUADC1 …` | `VAR_MAIZE_SPRH1_HYBRID` | Maize – SPRH1 Hybrid |
| 258 | `Maize - BHQP548 (CML144/CML159/CML176 X …` | `VAR_MAIZE_BHQP548` | Maize – BHQP548 |
| 259 | `Maize - Gibe3 Open Pollinated …` | `VAR_MAIZE_GIBE3_OPEN_POLLINATED` | Maize – Gibe3 Open Pollinated |
| 263 | `Common bean/Haricot bean - Wabero …` | `VAR_COMMON_BEAN_WABERO` | Common/Haricot/ bean – Wabero |
| 265 | `Common bean/Haricot bean - Gobu …` | `VAR_COMMON_BEAN_GOBU` | Common/Haricot/ bean – Gobu |
| 268 | `Common bean/Haricot bean - DOYO …` | `VAR_COMMON_BEAN_DOYO` | Common/Haricot/ bean – DOYO |
| 272 | `Faba Bean - ASHEBEKA (አሸበቃ) …` | `VAR_FABA_BEAN_ASHEBEKA` | Faba bean – ASHEBEKA |
| 273 | `Faba Bean - HASHENGE (ILB …` | `VAR_FABA_BEAN_HASHENGE` | Faba bean – HASHENGE |
| 275 | `Field pea - BURSA (ቡርሣ) …` | `VAR_FIELD_PEA_BURSA` | Field pea – BURSA |
| 279 | `Lentil - Jiru (R-186 X …` | `VAR_LENTIL_JIRU` | Lentil – Jiru |
| 287 | `Tef - Dagem [DZ-Cr-438 (RIL …` | `VAR_TEFF_DAGEM` | Tef – Dagem |
| 289 | `Linseed - Yadanno (H31 X …` | `VAR_LINSEED_YADANNO` | Linseed – Yadanno |
| 290 | `Bread Wheat - WANE (ETBW …` | `VAR_BREAD_WHEAT_WANE` | Bread Wheat – WANE |
| 293 | `Bread Wheat - LEMU (ETBW …` | `VAR_BREAD_WHEAT_LEMU` | Bread Wheat – LEMU |
| 301 | `Low land rice - Fogera2 …` | `VAR_RICE_FOGERA2` | Rice – Fogera2 |
| 328 | `Finger millet - መባ (GBK- …` | `VAR_FINGER_MILLET_MEBA` | Finger Millet – Meba |
| 331 | `Finger Millet - አክሱም (ACC …` | `VAR_FINGER_MILLET_AXUM` | Finger Millet – Axum |
| 332 | `Finger Millet - Diga-1 (ACC. …` | `VAR_FINGER_MILLET_DIGA_1` | Finger Millet – Diga-1 |
| 333 | `Finger Millet - Urji (Acc. …` | `VAR_FINGER_MILLET_URJI` | Finger Millet – Urji |
| 340 | `Faba Bean - Mosisaa (: …` | `VAR_FABA_BEAN_MOSISAA` | Faba bean – Mosisaa |
| 344 | `Field pea - ICN Bunsi …` | `VAR_FIELD_PEA_ICN_BUNSI` | Field pea – ICN Bunsi |
| 351 | `Lentil - Dembi (El – …` | `VAR_LENTIL_DEMBI` | Lentil – Dembi |
| 359 | `Linseed - Furtu (CI-1525 X …` | `VAR_LINSEED_FURTU` | Linseed – Furtu |
| 362 | `Faba bean - Numan (ኑማን) …` | `VAR_FABA_BEAN_NUMAN` | Faba bean – Numan |
| 364 | `Chickpea - Dimtu ( DZ-2012 …` | `VAR_CHICKPEA_DIMTU` | Chickpea – Dimtu |
| 367 | `Chickpea - (Hora) DZ-2012 CK-001/FLIP …` | `VAR_CHICKPEA_HORA` | Chickpea – Hora (DZ-2012 CK-001/FLIP) |
| 370 | `Chickpea - (Dhera) DZ-2012 CK-009/FLIP …` | `VAR_CHICKPEA_DHERA` | Chickpea – Dhera (DZ-2012 CK-009/FLIP) |
| 371 | `Faba bean - Walki (EH96049-2) …` | `VAR_FABA_BEAN_WALKI` | Faba bean – Walki (EH96049-2) |
| 380 | `Linseed - Kuma/ ኩማ (R734D …` | `VAR_LINSEED_KUMA` | Linseed – Kuma |
| 394 | `Bread Wheat - Sanate (14F/HAR …` | `VAR_BREAD_WHEAT_SANATE` | Bread Wheat – Sanate |
| 395 | `Bread Wheat - BIQA (ETBW …` | `VAR_BREAD_WHEAT_BIQA` | Bread Wheat – BIQA |
| 396 | `Bread Wheat - HONQOLO (ETBW …` | `VAR_BREAD_WHEAT_HONQOLO` | Bread Wheat – HONQOLO |
| 404 | `Sorghum - ESH-3 (Ethiopian Sorghum …` | `VAR_SORGHUM_ESH_3` | Sorghum – ESH-3 |
| 411 | `Faba bean - GORA (EK …` | `VAR_FABA_BEAN_GORA` | Faba bean – GORA |
| 424 | `Common bean/Haricot bean - Remeda …` | `VAR_COMMON_BEAN_REMEDA` | Common/Haricot/ bean – Remeda |
| 484 | `Bread Wheat - Hoggana (ETBW …` | `VAR_BREAD_WHEAT_HOGGANA` | Bread Wheat – Hoggana |
| 485 | `Bread Wheat - Shorima (ETBW …` | `VAR_BREAD_WHEAT_SHORIMA` | Bread Wheat – Shorima |
| 494 | `Durem Wheat - Asasa (DZ …` | `VAR_DURUM_WHEAT_ASASA` | Durum Wheat – Asasa |
| 495 | `Durem Wheat - Arsi-Robe (TOB …` | `VAR_DURUM_WHEAT_ARSI_ROBE` | Durum Wheat – Arsi-Robe |
| 497 | `Durem Wheat - Bichena (DZ …` | `VAR_DURUM_WHEAT_BICHENA` | Durum Wheat – Bichena |
| 498 | `Durem Wheat - Kilinto (DZ …` | `VAR_DURUM_WHEAT_KILINTO` | Durum Wheat – Kilinto |
| 501 | `Durem Wheat - Yerer (CD …` | `VAR_DURUM_WHEAT_YERER` | Durum Wheat – Yerer |
| 503 | `Durem Wheat - Laste (Tob …` | `VAR_DURUM_WHEAT_LASTE` | Durum Wheat – Laste |
| 504 | `Durem Wheat - Selam (DZ …` | `VAR_DURUM_WHEAT_SELAM` | Durum Wheat – Selam |
| 505 | `Durem Wheat - Mettaya (DZ …` | `VAR_DURUM_WHEAT_METTAYA` | Durum Wheat – Mettaya |
| 506 | `Durem Wheat - Mosobo (DZ …` | `VAR_DURUM_WHEAT_MOSOBO` | Durum Wheat – Mosobo |
| 507 | `Durem Wheat - Megenagna (DZ …` | `VAR_DURUM_WHEAT_MEGENAGNA` | Durum Wheat – Megenagna |
| 508 | `Durem Wheat - Ilani (DZ …` | `VAR_DURUM_WHEAT_ILANI` | Durum Wheat – Ilani |
| 509 | `Durem Wheat - Oda (DZ …` | `VAR_DURUM_WHEAT_ODA` | Durum Wheat – Oda |
| 510 | `Durem Wheat - Malefia- (CD …` | `VAR_DURUM_WHEAT_MALEFIA` | Durum Wheat – Malefia |
| 512 | `Durem Wheat - Bakalcha (980SN …` | `VAR_DURUM_WHEAT_BAKALCHA` | Durum Wheat – Bakalcha |
| 513 | `Durem Wheat - EJERSA LABUD/NIGERIS …` | `VAR_DURUM_WHEAT_EJERSA_LABUD_NIGERIS` | Durum Wheat – EJERSA LABUD/NIGERIS |
| 514 | `Durem Wheat - OBSA (ALTAR …` | `VAR_DURUM_WHEAT_OBSA` | Durum Wheat – OBSA |
| 529 | `Bread Wheat - Mekelle- 03 …` | `VAR_BREAD_WHEAT_MEKELLE_03` | Bread Wheat – Mekelle-03 |
| 530 | `Durum Wheat - Mukiye (STJ3/BCR …` | `VAR_DURUM_WHEAT_MUKIYE` | Durum Wheat – Mukiye |
| 531 | `Durum Wheat - Mangudo (ICAJIHAN …` | `VAR_DURUM_WHEAT_MANGUDO` | Durum Wheat – Mangudo |
| 546 | `Maize - BH-541 (NSCM-41-188/32/ X …` | `VAR_MAIZE_BH_541` | Maize – BH-541 |
| 548 | `Maize - BH-QP-542 (CML-144XCML-159 X …` | `VAR_MAIZE_BH_QP_542` | Maize – BH-QP-542 |
| 553 | `Maize - Beles SC 713 …` | `VAR_MAIZE_BELES_SC_713` | Maize – Beles SC 713 |
| 554 | `Maize - Bereda SC 715 …` | `VAR_MAIZE_BEREDA_SC_715` | Maize – Bereda SC 715 |
| 556 | `Maize - BH -543 (SC-22 …` | `VAR_MAIZE_BH_543` | Maize – BH-543 |
| 558 | `Maize - Hora (Ambo 2 …` | `VAR_MAIZE_HORA` | Maize – Hora |
| 564 | `Food barley - Fetina (SXH, …` | `VAR_BARLEY_FETINA` | Food Barley – Fetina |
| 568 | `Maize - Bako-1 SC-22XFH-625-263 XCML …` | `VAR_MAIZE_BAKO_1_SC_22XFH_625_263_XCML` | Maize – Bako-1 SC-22XFH-625-263 XCML |
| 570 | `Maize - Aba raya (Sc …` | `VAR_MAIZE_ABA_RAYA` | Maize – Aba raya |
| 575 | `Field pea - BILALLO (EH …` | `VAR_FIELD_PEA_BILALLO` | Field pea – BILALLO |
| 576 | `Field pea - Haranna (Cool …` | `VAR_FIELD_PEA_HARANNA` | Field pea – Haranna |
| 577 | `Field pea - Teshale (EH99005-7 …` | `VAR_FIELD_PEA_TESHALE` | Field pea – Teshale |
| 583 | `Maize - Melkasa-6Q (Pool 15 …` | `VAR_MAIZE_MELKASA_6Q` | Maize – Melkasa-6Q |
| 584 | `Maize - Melkasa-7 (Pop 147 …` | `VAR_MAIZE_MELKASA_7` | Maize – Melkasa-7 |
| 587 | `Maize - MH 130 (CML440/CML445/ …` | `VAR_MAIZE_MH_130` | Maize – MH 130 |
| 596 | `Sorghum - Baji (85 MW …` | `VAR_SORGHUM_BAJI` | Sorghum – Baji |
| 597 | `Sorghum - MEKO-1 (M – …` | `VAR_SORGHUM_MEKO_1` | Sorghum – MEKO-1 |
| 603 | `Sorghum - Yeju (ICSV 111 …` | `VAR_SORGHUM_YEJU` | Sorghum – Yeju |
| 607 | `Sorghum - Hormat -- (ICSV …` | `VAR_SORGHUM_HORMAT` | Sorghum – Hormat |
| 612 | `Sorghum - MISKIR (PGRC/E#69441XP-9401) (Early …` | `VAR_SORGHUM_MISKIR` | Sorghum – MISKIR (PGRC/E#69441XP-9401) (Early) |
| 616 | `Sorghum - RED SWAZI (Malting …` | `VAR_SORGHUM_RED_SWAZI` | Sorghum – RED SWAZI |
| 617 | `Sorghum - GEREMEW (87 BK …` | `VAR_SORGHUM_GEREMEW` | Sorghum – GEREMEW |
| 622 | `Food Barley - Meserach (Kulumsa …` | `VAR_BARLEY_MESERACH` | Food Barley – Meserach |
| 633 | `Faba bean - Tesfa (75 …` | `VAR_FABA_BEAN_TESFA` | Faba bean – Tesfa |
| 640 | `Field pea - Tulu (PGRC/E32 …` | `VAR_FIELD_PEA_TULU` | Field pea – Tulu |
| 652 | `Field pea - Weyitu (EH …` | `VAR_FIELD_PEA_WEYITU` | Field pea – Weyitu |
| 680 | `Linseed - Berene (PGRC/E 01 …` | `VAR_LINSEED_BERENE` | Linseed – Berene |
| 701 | `Common bean - Hora (ሆራ) …` | `VAR_COMMON_BEAN_HORA` | Common/Haricot/ bean – Hora |
| 702 | `Common bean/Haricot bean - DAB-413 …` | `VAR_COMMON_BEAN_DAB_413` | Common/Haricot/ bean – DAB-413 |
| 704 | `Common bean/Haricot bean- (Hundaf) (ሁንዳፍ) …` | `VAR_COMMON_BEAN_HUNDAF` | Common/Haricot/ bean – Hundaf |
| 711 | `Bread Wheat - Mitike (HAR …` | `VAR_BREAD_WHEAT_MITIKE` | Bread Wheat – Mitike |
| 743 | `Common bean - Hirna (ECAB …` | `VAR_COMMON_BEAN_HIRNA` | Common/Haricot/ bean – Hirna |
| 750 | `Emmer wheat/Aja - Sinana-01 (Acc. …` | `VAR_EMMER_WHEAT_SINANA_01` | Emmer wheat (Aja) – Sinana-01 |
| 758 | `Common bean/Haricot bean - (Keyyo) …` | `VAR_COMMON_BEAN_KEYYO` | Common/Haricot/ bean – Keyyo |
| 760 | `Common bean/Haricot bean -- Hundane …` | `VAR_COMMON_BEAN_HUNDANE` | Common/Haricot/ bean – Hundane |
| 763 | `Common bean/Haricot bean - Awash …` | `VAR_COMMON_BEAN_AWASH_1` | Common/Haricot/ bean – Awash-1 |
| 764 | `Common bean - Melka Awash-98 …` | `VAR_COMMON_BEAN_MELKA_AWASH_98` | Common/Haricot/ bean – Melka Awash-98 |
| 765 | `Common bean - Nazareth-2 (TA04JI) …` | `VAR_COMMON_BEAN_NAZARETH_2` | Common/Haricot/ bean – Nazareth-2 (TA04JI) |
| 767 | `Common bean - Red Wolaita- …` | `VAR_COMMON_BEAN_RED_WOLAITA` | Common/Haricot/ bean – Red Wolaita |
| 768 | `Common bean - Atndaba /A-262/- …` | `VAR_COMMON_BEAN_ATNDABA_A_262` | Common/Haricot/ bean – Atndaba /A-262 |
| 769 | `Common bean - Gofta- Food …` | `VAR_COMMON_BEAN_GOFTA` | Common/Haricot/ bean – Gofta |
| 770 | `Common bean - Ayenew- Food …` | `VAR_COMMON_BEAN_AYENEW` | Common/Haricot/ bean – Ayenew |
| 771 | `Common bean - Melke/Areka 97 …` | `VAR_COMMON_BEAN_MELKE_AREKA_97` | Common/Haricot/ bean – Melke/Areka 97 |
| 772 | `Common bean - Beshbesh/Melk 97 …` | `VAR_COMMON_BEAN_BESHBESH_MELK_97` | Common/Haricot/ bean – Beshbesh/Melk 97 |
| 773 | `Common bean - Gobe Rasha-1(ICA-15541) …` | `VAR_COMMON_BEAN_GOBE_RASHA_1` | Common/Haricot/ bean – Gobe Rasha-1 (ICA-15541) |
| 777 | `CML 395 X CML 202 …` | `VAR_MAIZE_CML_395_X_CML_202` | Maize – CML 395 X CML 202 |
| 880 | `faba bean - dagm (Grarjarso …` | `VAR_FABA_BEAN_DAGM` | Faba bean – Dagm |
| 915 | `Sweet potato (Ipomoea batatas)-NASPOT-12 (Orange …` | `VAR_SWEET_POTATO_NASPOT_12` | Sweet potato – NASPOT-12 |
| 918 | `Tomato -Jorgie-1 (Wonhong No.3) Cherry …` | `VAR_TOMATO_JORGIE_1_CHERRY` | Tomato – Jorgie-1 (Wonhong No.3) Cherry |

## 4. Merged Duplicate Rows

| Row ID | Source Name | Merged Into Code |
|---|---|---|
| 107 | `Maize- BH520 W1 (Nada)` | `VAR_MAIZE_BH520_W1` |
| 198 | `Bread Wheat - Deka (ETBW …` | `VAR_BREAD_WHEAT_DEKA` |
| 249 | `Bread Wheat - Fentale (MOONTIJ-3 …` | `VAR_BREAD_WHEAT_FENTALE` |
| 325 | `Maize - CPS.6` | `VAR_MAIZE_CPS_6` |
| 326 | `Maize - CPS.10` | `VAR_MAIZE_CPS_10` |
| 402 | `Maize -Melkasa-1Q` | `VAR_MAIZE_MELKASA_1Q` |
| 403 | `Maize - Mh140 (Melkasa Hybrid …` | `VAR_MAIZE_MH140` |
| 405 | `Sorghum - PAC 537` | `VAR_SORGHUM_PAC_537` |
| 527 | `Bread Wheat - Ogolcho (ETBW5520)` | `VAR_BREAD_WHEAT_OGOLCHO` |
| 726 | `Bread Wheat-Guna (HAR-2029)` | `VAR_BREAD_WHEAT_GUNA` |
| 727 | `Bread Wheat-Dure (HAR-1008)` | `VAR_BREAD_WHEAT_DURE` |
| 728 | `Bread Wheat-KBG-01 (FH-1-7A or Line …` | `VAR_BREAD_WHEAT_KBG_01` |
| 731 | `Bread Wheat-Densa (HAR-2562)` | `VAR_BREAD_WHEAT_DENSA` |
| 732 | `Bread Wheat-Bobicho (HAR-2419)` | `VAR_BREAD_WHEAT_BOBICHO` |
| 733 | `Bread Wheat-Tossa (HAR 3123)` | `VAR_BREAD_WHEAT_TOSSA` |
| 734 | `Bread Wheat-Digalu (SHA 7/ KAUZ …` | `VAR_BREAD_WHEAT_DIGALU` |
| 735 | `Bread Wheat-Senkegna (HAR 3646)` | `VAR_BREAD_WHEAT_SENKEGNA` |
| 736 | `Bread Wheat-TAY (ET-12 D4/HAR 604 …` | `VAR_BREAD_WHEAT_TAY` |
| 737 | `Bread Wheat-Meraro (11-6-24)` | `VAR_BREAD_WHEAT_MERARO` |
| 738 | `Bread Wheat-Warkaye (HAR-3820)` | `VAR_BREAD_WHEAT_WARKAYE` |
| 739 | `Bread Wheat-Jiru (HAR-2896)` | `VAR_BREAD_WHEAT_JIRU` |
| 742 | `Common bean/Haricot bean - Fedis …` | `VAR_COMMON_BEAN_FEDIS` |
| 826 | `mungbean- Arkebe` | `VAR_MUNG_BEAN_ARKEBE` |
| 831 | `Gishama (PR-143-(26))` | `VAR_SOYBEAN_GISHAMA` |
| 832 | `Malt barley- HB1963` | `VAR_MALT_BARLEY_HB1963` |
| 833 | `Malt barley- HB1964` | `VAR_MALT_BARLEY_HB1964` |
| 852 | `Haro (FMC-33) Landrace` | `VAR_FINGER_MILLET_HARO` |
| 876 | `Tef- koye (DZ-01-1285)` | `VAR_TEFF_KOYE` |
| 877 | `Tef- gerado (DZ- 01-1281)` | `VAR_TEFF_GERADO` |
| 888 | `soyabean- ETHIO- YUGOSLAVIA` | `VAR_SOYBEAN_ETHIO_YUGOSLAVIA` |
| 890 | `haricot bean- melka awash -98` | `VAR_COMMON_BEAN_MELKA_AWASH_98` |
| 896 | `lentil- Ada` | `VAR_LENTIL_ADA` |
| 908 | `sesame-Sifan (Accession HSc-016#13)` | `VAR_SESAME_SIFAN` |

## 5. Omitted Rows Summary

- **Nameless rows (38)**: `[35, 36, 37, 38, 39, 132, 133, 134, 136, 137, 138, 139, 159, 222, 223, 224, 225, 226, 228, 229, 281, 282, 291, 292, 353, 354, 355, 418, 425, 426, 665, 666, 667, 668, 681, 682, 683, 761]`
- **Mid-cut unresolvable rows (11)**: `[46, 48, 70, 84, 119, 423, 480, 511, 561, 762, 766]`
- **Crop-only rows (8)**: `[92, 775, 779, 805, 807, 808, 868, 902]` (Sorghum, Onion, Tomato, Faba bean, Pigeon pea, Food barley, Cacao, Groundnut)
- **Maize parental lines (14)**: `[776, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 897]`
- **Base pack duplicates (7)**: `[321, 478, 479, 524, 580, 780, 781]` (including `Danda'a` and `Kakaba`)
