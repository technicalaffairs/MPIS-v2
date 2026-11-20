#!/usr/bin/env python3
"""Translate the 7 pumps/generators/fans/filters docs (the group whose
workers errored twice) into faithful technical Arabic.

Approach: the two procedures (P-000-TEMP, P-316) are translated by hand
below, section by section. The four index pages are mostly tables of
equipment names / manufacturers / codes / stations, so they are translated
with a phrase glossary (longest match first, case-insensitive); proper
names, manufacturers, model codes, interval codes (M1/Y1/H1500) and
station names stay in Latin script, exactly as in the source.
Units in compact table strings stay Latin; units in full sentences are
translated (m3/ساعة، ك.و.، فولت).
"""
import json, os, re, sys

ROOT = "/home/hatch/workspace/mpis-v2"
OUT = os.path.join(ROOT, "tools", "translation41")

# ---------------------------------------------------------------- glossary
# (english phrase, arabic phrase). Applied longest-first, case-insensitive.
GLOSSARY = [
    # nav labels
    ("Home", "الرئيسية"), ("About us", "من نحن"), ("Forms", "النماذج"),
    ("Admin", "الإدارة"), ("Status", "الحالة"), ("Draf docs", "مسودات المستندات"),
    ("Prod", "الإنتاج"), ("Trans", "النقل"), ("Dist", "التوزيع"),
    ("Ad docs", "المستندات المعتمدة"),
    ("Click links below to access desired document", "انقر على الروابط أدناه للوصول إلى المستند المطلوب"),
    # pumps — full phrases first
    ("Boiler Feed Water Pump, Multi Stage Horizontal Centrifugal Pump, MES 125-10, Termomeccanica, Italiana",
     "مضخة مياه تغذية الغلاية، مضخة طرد مركزي أفقية متعددة المراحل، MES 125-10، Termomeccanica، Italiana"),
    ("Boiler Feed Water Pump, Horizontal Centrifugal 5BB8I510, Transamerica Deleval",
     "مضخة مياه تغذية الغلاية، طرد مركزي أفقية 5BB8I510، Transamerica Deleval"),
    ("Boiler Feed Water Pump, Multi Stage Horizontal Centrifugal Pump",
     "مضخة مياه تغذية الغلاية، مضخة طرد مركزي أفقية متعددة المراحل"),
    ("Boiler Feed Water Pumps, 1,2AE- PO1&2, KSB", "مضخات مياه تغذية الغلاية، 1,2AE- PO1&2، KSB"),
    ("Boiler Feed Water Pump", "مضخة مياه تغذية الغلاية"),
    ("Boiler Feed Pump", "مضخة تغذية الغلاية"),
    ("Boiler Feed Pumps", "مضخات تغذية الغلاية"),
    ("Turbine Generator", "مولد التوربينات"),
    ("Hydrogen Cooled Turbine Generator", "مولد توربين مبرد بالهيدروجين"),
    ("Cylindrical Rotor", "دوار أسطواني"),
    ("Discharge Press", "ضغط الطرد"),
    ("Fire Pump", "مضخة إطفاء"),
    ("Mixed Flow Pump", "مضخة تدفق مختلط"),
    ("Emergency Oil Pump", "مضخة زيت طوارئ"),
    ("Brine Recirculation Pump", "مضخة إعادة تدوير محلول ملحي"),
    ("Soduim Hypochlorite Production Unit", "وحدة إنتاج هيبوكلوريت الصوديوم"),
    ("Soduim Hypochorite Production Unit", "وحدة إنتاج هيبوكلوريت الصوديوم"),
    ("Static (3 ph full bridge)", "ستاتيكي (جسر كامل ثلاثي الأطوار)"),
    ("Static", "ستاتيكي"),
    ("and its Motor", "ومحركها"),
    ("1000A of GT Siemens 1000A", "1000A للتوربين الغازي Siemens 1000A"),
    ("and", "و"),
    ("or", "أو"),
    ("Boiler Feed Water Pumps", "مضخات مياه تغذية الغلاية"),
    ("High Pressure Feed Water Pump", "مضخة مياه تغذية عالية الضغط"),
    ("Low Pressure Feed Water Pump", "مضخة مياه تغذية منخفضة الضغط"),
    ("High Feed Water Pump", "مضخة مياه تغذية عالية"),
    ("Feed Water Pump for Water Treatment Plant", "مضخة مياه تغذية لمحطة معالجة المياه"),
    ("Feed Water Pump, Multi Stage Horizontal Centrifugal", "مضخة مياه تغذية، طرد مركزي أفقية متعددة المراحل"),
    ("Feed Water Pump, 150-CHM-280-18-8-UC-OO, Sigma Lutin", "مضخة مياه تغذية، 150-CHM-280-18-8-UC-OO، Sigma Lutin"),
    ("Feed Water Pump", "مضخة مياه تغذية"),
    ("Mazout fuel Oil Transfer Pump,3/Unit,Transamerica deleval", "مضخة نقل زيت وقود المازوت، 3/وحدة، Transamerica deleval"),
    ("Mazout fuel Oil Transfer Pump 3/Unit", "مضخة نقل زيت وقود المازوت 3/وحدة"),
    ("Mazout Transfer pump for daily tank", "مضخة نقل مازوت للخزان اليومي"),
    ("Mazout Transfer Pump for Daily tank", "مضخة نقل مازوت للخزان اليومي"),
    ("Mazout Transfer Pump", "مضخة نقل مازوت"),
    ("Mazout unloading Pump", "مضخة تفريغ مازوت"),
    ("Mazout Burner, Stripping, Solar Stripping, Igniter, aux. Boiler Solar transfer Pumps",
     "مضخة حارق مازوت، تجريد، تجريد شمسي، مشعل، مضخات نقل شمسية للغلاية المساعدة"),
    ("Mazout Forwarding & Recirculating Pump", "مضخة إرسال وإعادة تدوير مازوت"),
    ("Mazout Forwarding Pump", "مضخة إرسال مازوت"),
    ("Burner Mazout Pumps, Fuel oil Unloading Pumps", "مضخات مازوت الحارقات، مضخات تفريغ زيت الوقود"),
    ("Burner Mazout Pumps, Fuel unloading pump", "مضخات مازوت الحارقات، مضخة تفريغ وقود"),
    ("Burner Fuel Oil Pumps, Rotary Screw Pumps", "مضخات زيت وقود الحارقات، مضخات حلزونية دوارة"),
    ("Burner Fuel Oil Pumps", "مضخات زيت وقود الحارقات"),
    ("Closed Cooling Pump, 3416, Goulds Pumps", "مضخة التبريد المغلق، 3416، Goulds Pumps"),
    ("Closed Cooling Pump", "مضخة التبريد المغلق"),
    ("Closed cooling water Pump, Single stage horizontal, Centrifugal Pump",
     "مضخة مياه التبريد المغلق، أحادية المرحلة أفقية، مضخة طرد مركزي"),
    ("Closed cooling water Pump", "مضخة مياه التبريد المغلق"),
    ("Closed Cooling Water Pump", "مضخة مياه التبريد المغلق"),
    ("Service Water Pump", "مضخة مياه الخدمة"),
    ("Desalination Water Supply Pump", "مضخة إمداد مياه التحلية"),
    ("Condensate Extraction Pump Multi-Stage Vertical Centrifugal Pump",
     "مضخة استخلاص مكثفات طرد مركزي رأسية متعددة المراحل"),
    ("Condensate Extraction Pump, Multi-stage vertical centrifugal pump",
     "مضخة استخلاص مكثفات، مضخة طرد مركزي رأسية متعددة المراحل"),
    ("Condensate Extraction Pump, Multi-stage Vertical Centrifugal Pump",
     "مضخة استخلاص مكثفات، مضخة طرد مركزي رأسية متعددة المراحل"),
    ("Condensate Extraction Pump, and its Motor", "مضخة استخلاص مكثفات ومحركها"),
    ("Condensate Extraction Pump", "مضخة استخلاص مكثفات"),
    ("Condensate Pump, Centrifugal Vertical can", "مضخة مكثفات، طرد مركزي رأسية"),
    ("Condensate Pump 2nd Stage", "مضخة مكثفات المرحلة الثانية"),
    ("Condensate Pump 1st stage", "مضخة مكثفات المرحلة الأولى"),
    ("Condensate Pump", "مضخة مكثفات"),
    ("Condensate Transfer Pump, Horizontal Centrifugal", "مضخة نقل مكثفات، طرد مركزي أفقية"),
    ("Condensate Transfer Pump, Centrifugal", "مضخة نقل مكثفات، طرد مركزي"),
    ("Condensate Transfer Pump", "مضخة نقل مكثفات"),
    ("Main Circulating Water Pump", "مضخة المياه المتداولة الرئيسية"),
    ("Circulating water pump", "مضخة المياه المتداولة"),
    ("Circulating Water Pump", "مضخة المياه المتداولة"),
    ("Circulate Water Pump", "مضخة تدوير مياه"),
    ("Condensate Water Pump", "مضخة مياه مكثفات"),
    ("Boiler Circulating Pump Single", "مضخة تدوير غلاية أحادية"),
    ("Stator Circulating Pump, Horizontal Centrifugal", "مضخة تدوير الجزء الثابت، طرد مركزي أفقية"),
    ("Stator Circulating Pump", "مضخة تدوير الجزء الثابت"),
    ("Stator Circulating Water Pump", "مضخة مياه تدوير الجزء الثابت"),
    ("Turbine Water Circulating Pump for Gas Turbine frame 5", "مضخة تدوير مياه التوربين للتوربين الغازي إطار 5"),
    ("Turbine Water Circulating Pump", "مضخة تدوير مياه التوربين"),
    ("Main Cooling Water Pump, Centrifugal Pump Single Stage", "مضخة مياه التبريد الرئيسية، مضخة طرد مركزي أحادية المرحلة"),
    ("Main Cooling Water Pump", "مضخة مياه التبريد الرئيسية"),
    ("Main Cooling Pump for Condenser", "مضخة التبريد الرئيسية للمكثف"),
    ("Cooling Water Pump, Horizontal Centrifugal Single Stage HC", "مضخة مياه تبريد، طرد مركزي أفقية أحادية المرحلة HC"),
    ("Cooling Water Pump, 1000 BQDV-1290-36-LU-00,Sigma", "مضخة مياه تبريد، 1000 BQDV-1290-36-LU-00، Sigma"),
    ("Cooling Water Pump", "مضخة مياه تبريد"),
    ("Lubricating Water Pump, Centrifugal Horizontal Single Stage", "مضخة مياه تزييت، طرد مركزي أفقية أحادية المرحلة"),
    ("Lubricating Water Pump", "مضخة مياه تزييت"),
    ("Raw water Pump, Ver. centrifugal Pump", "مضخة مياه خام، مضخة طرد مركزي رأسية"),
    ("Raw water Pump", "مضخة مياه خام"),
    ("Mixed bed caustic dosing PUMP", "مضخة جرعات الصودا الكاوية للطبقة المختلطة"),
    ("Sludge oil separation pump", "مضخة فصل زيت الحمأة"),
    ("Polishing filler feed pump", "مضخة تغذية مرشح التلميع"),
    ("Condenser vacuum PUMP", "مضخة تفريغ المكثف"),
    ("Manhole 11 PUMP", "مضخة فتحة التفتيش 11"),
    ("Sodium hypochlorite injection pump", "مضخة حقن هيبوكلوريت الصوديوم"),
    ("Polymer dosing pump for filter press", "مضخة جرعات البوليمر لمكبس الترشيح"),
    ("Water-Air pump vertical mixed-flow pump", "مضخة مياه-هواء رأسية مختلطة التدفق"),
    ("Water-Air pump", "مضخة مياه-هواء"),
    ("Leakage Oil Pump", "مضخة زيت التسرب"),
    ("Extraction Condensate Pump", "مضخة استخلاص مكثفات"),
    ("Screw Spindle Pump, Heavy Fuel Oil H.P & LP Pump", "مضخة حلزونية لولبية، مضخة زيت وقود ثقيل ضغط عالٍ ومنخفض"),
    ("Screw Spindle Pump", "مضخة حلزونية لولبية"),
    ("Screw pump For Mazout oil", "مضخة حلزونية لزيت المازوت"),
    ("Screw Pump For Mazout Oil", "مضخة حلزونية لزيت المازوت"),
    ("Unloading Screw Pumps", "مضخات حلزونية للتفريغ"),
    ("Oil Pump for Sediment", "مضخة زيت للرواسب"),
    ("Booster Oil Pump (Low pressure Pump of Mazout)", "مضخة زيت معززة (مضخة مازوت منخفضة الضغط)"),
    ("Fuel Oil Booster Pump, Horizontal Centrifugal", "مضخة تعزيز زيت الوقود، طرد مركزي أفقية"),
    ("Fuel Oil Booster Pump", "مضخة تعزيز زيت الوقود"),
    ("Fuel Oil Transfer Pump", "مضخة نقل زيت الوقود"),
    ("Fuel Oil Pumps", "مضخات زيت الوقود"),
    ("Main Fuel Oil Pump", "مضخة زيت الوقود الرئيسية"),
    ("Igniter Fuel Oil Pump", "مضخة زيت وقود المشعل"),
    ("Blow Down Sump Pump", "مضخة حفرة النفخ"),
    ("Boiler Area Sump Pump, Vertical Centrifugal", "مضخة حفرة منطقة الغلاية، طرد مركزي رأسية"),
    ("Boiler Area Sump Pump", "مضخة حفرة منطقة الغلاية"),
    ("Boiler Pit Sump Pump, Centrifugal", "مضخة حفرة الغلاية، طرد مركزي"),
    ("Boiler Pit Sump Pump", "مضخة حفرة الغلاية"),
    ("Wash Down Sump Pump, Centrifugal", "مضخة حفرة الغسيل، طرد مركزي"),
    ("Wash Down Sump Pump", "مضخة حفرة الغسيل"),
    ("Fire Fighting Pump Motor driven", "مضخة مكافحة حريق تعمل بمحرك"),
    ("Fire Fighting Pump, Horizontal-Multi Stage", "مضخة مكافحة حريق، أفقية متعددة المراحل"),
    ("Fire Fighting Pump, 250-CVEV-400-30/2, Sigma D. Benesov", "مضخة مكافحة حريق، 250-CVEV-400-30/2، Sigma D. Benesov"),
    ("Fire Fighting Pump, 250-QVD-570-50-LU, Sigma D. Benesov", "مضخة مكافحة حريق، 250-QVD-570-50-LU، Sigma D. Benesov"),
    ("Fire Fighting Pump", "مضخة مكافحة حريق"),
    ("Vertical Centrifugal Pump for Fire Fighting System Jocky Pump", "مضخة طرد مركزي رأسية لنظام مكافحة الحريق، مضخة جوكي"),
    ("Horizontal Centrifugal Pump, for Fire Fighting System", "مضخة طرد مركزي أفقية لنظام مكافحة الحريق"),
    ("Foam Concentrate Pump for Fire Fighting Application", "مضخة مركز الرغوة لتطبيقات مكافحة الحريق"),
    ("Foam Concentrate Pump, for Fire Fighting Application", "مضخة مركز الرغوة لتطبيقات مكافحة الحريق"),
    ("Foam Concentrate Pump", "مضخة مركز الرغوة"),
    ("Main Lube Pump", "مضخة التزييت الرئيسية"),
    ("Main Lube Oil Pump", "مضخة زيت التزييت الرئيسية"),
    ("Lube Oil Pump", "مضخة زيت تزييت"),
    ("Auxiliary Lube Oil Pump", "مضخة زيت التزييت المساعدة"),
    ("High pressure pump, Radial piston, Two banks, 5 cylinders, Max. working pressure 200 Bar",
     "مضخة ضغط عالٍ، مكبس شعاعي، صفان، 5 أسطوانات، أقصى ضغط تشغيل 200 بار"),
    ("High pressure pump", "مضخة ضغط عالٍ"),
    ("Back wash ver. centrifugal pump", "مضخة غسيل عكسي طرد مركزي رأسية"),
    ("Drainage Pump, CP3201MT120, FLYGT", "مضخة صرف، CP3201MT120، FLYGT"),
    ("Drainage Pump", "مضخة صرف"),
    ("Dewatering Pump, Centrifugal", "مضخة نزح مياه، طرد مركزي"),
    ("Dewatering Pump", "مضخة نزح مياه"),
    ("Grease Pump", "مضخة شحم"),
    ("Vacuum Pump", "مضخة تفريغ"),
    ("JOCKEY Pump", "مضخة جوكي"),
    ("Jocky Pump", "مضخة جوكي"),
    ("Booster Pump", "مضخة تعزيز"),
    ("Hydraulic Pump Unit", "وحدة مضخة هيدروليكية"),
    ("Chemical Transfer Pump, Vertical Centrifugal", "مضخة نقل مواد كيميائية، طرد مركزي رأسية"),
    ("Chemical Transfer Pump", "مضخة نقل مواد كيميائية"),
    ("Metering Pump, Positive Displacement Diaphragm", "مضخة قياس، إزاحة موجبة بغشاء"),
    ("Metering Pump", "مضخة قياس"),
    ("Caustic Dissolver Pump, Horizontal Centrifugal", "مضخة إذابة الصودا الكاوية، طرد مركزي أفقية"),
    ("Caustic Dissolver Pump", "مضخة إذابة الصودا الكاوية"),
    ("Boiler Fill and Wash Pump, Horizontal Centrifugal", "مضخة ملء وغسيل الغلاية، طرد مركزي أفقية"),
    ("Boiler Fill and Wash Pump", "مضخة ملء وغسيل الغلاية"),
    ("Piston Diaphragm Pump, Positive Displacement", "مضخة مكبس بغشاء، إزاحة موجبة"),
    ("Piston Diaphragm Pump", "مضخة مكبس بغشاء"),
    ("Goulds Vertical Pump, Vertical Centrifugal", "مضخة Goulds رأسية، طرد مركزي رأسية"),
    ("Thrust Guide Bearing Oil Pump", "مضخة زيت محمل التوجيه الدفعي"),
    ("Thrust Guide Bearing Oil", "زيت محمل التوجيه الدفعي"),
    ("Clear Water Pump, Intermediate Pump, Make Up Water Pump, Regeneration Pump, Drinking Water Pump",
     "مضخة مياه نظيفة، مضخة وسيطة، مضخة مياه تعويضية، مضخة تجديد، مضخة مياه شرب"),
    ("Clear Water Pump", "مضخة مياه نظيفة"),
    ("Intermediate Pump", "مضخة وسيطة"),
    ("Make Up Water Pump", "مضخة مياه تعويضية"),
    ("Regeneration Pump", "مضخة تجديد"),
    ("Drinking Water Pump", "مضخة مياه شرب"),
    ("Washing Pump, Centrifugal Pump, Single Stage", "مضخة غسيل، مضخة طرد مركزي، أحادية المرحلة"),
    ("Washing Pump", "مضخة غسيل"),
    ("Filtering Water Pump", "مضخة مياه ترشيح"),
    ("Sewage and Drainage Pumps", "مضخات الصرف الصحي والصرف"),
    ("Sewage and Drainage Pumps, CP3126MT181, FLYGT", "مضخات الصرف الصحي والصرف، CP3126MT181، FLYGT"),
    ("Vertical SubMerged Lube Oil single stage, Centrifugal Pumps Bofflo Co",
     "مضخات زيت تزييت مغمورة رأسية أحادية المرحلة، طرد مركزي، Bofflo Co"),
    ("Liquid Ring Vacuum Pump", "مضخة تفريغ بحلقة سائلة"),
    ("Water Jet Air Pump", "مضخة هواء بنفث الماء"),
    ("Screen Wash Pumps", "مضخات غسيل الغرابيل"),
    ("Multi-stage vertical centrifugal pump", "مضخة طرد مركزي رأسية متعددة المراحل"),
    ("Multi-stage Vertical Centrifugal Pump", "مضخة طرد مركزي رأسية متعددة المراحل"),
    ("Multi Stage Horizontal Centrifugal", "طرد مركزي أفقية متعددة المراحل"),
    ("Multi-stage horizontal centrifugal pump", "مضخة طرد مركزي أفقية متعددة المراحل"),
    ("Single Stage Vertical", "أحادية المرحلة رأسية"),
    ("Single Stage Horizontal", "أحادية المرحلة أفقية"),
    ("Three Stage Air Filter", "فلتر هواء ثلاثي المراحل"),
    ("Multi-stage", "متعددة المراحل"),
    ("Multi Stage", "متعددة المراحل"),
    ("Single Stage", "أحادية المرحلة"),
    ("Vertical Centrifugal", "طرد مركزي رأسية"),
    ("Horizontal Centrifugal", "طرد مركزي أفقية"),
    ("Centrifugal Pump", "مضخة طرد مركزي"),
    ("Centrifugal", "طرد مركزي"),
    ("Vertical", "رأسية"),
    ("Horizontal", "أفقية"),
    # generators
    ("Carbon Brushes of Generator", "فرش كربونية للمولد"),
    ("Carbon Brushes", "فرش كربونية"),
    ("Carbon Brush", "فرشاة كربونية"),
    ("Brushes for Generators, Exciters, and Earthing", "فرش للمولدات والمُهيِّجات والتأريض"),
    ("Generator Exciter Brushes & Slip Rings", "فرش مُهيِّج المولد وحلقات الانزلاق"),
    ("Generator Exciter System", "نظام مُهيِّج المولد"),
    ("Generator Slip Ring and Exciter", "حلقة انزلاق المولد والمُهيِّج"),
    ("Generator Air Coolers", "مبردات هواء المولد"),
    ("Generator 3 ph Turbo Alternator", "مولد 3 ph توربيني متناوب"),
    ("Generator 3ph, turbo alternator", "مولد 3ph، مولد توربيني متناوب"),
    ("Generator H2 Cooling", "مولد بتبريد H2"),
    ("Hydrogen Cooled Generator", "مولد مبرد بالهيدروجين"),
    ("Hydrogen Generators", "مولدات هيدروجين"),
    ("Hydrogen Generator Plant", "محطة مولد هيدروجين"),
    ("Hydrogen Generation Plant", "محطة توليد هيدروجين"),
    ("Hydrogen Production Plant", "محطة إنتاج هيدروجين"),
    ("Hydrogen Production Unit", "وحدة إنتاج هيدروجين"),
    ("Emergency Diesel Generator", "مولد ديزل للطوارئ"),
    ("Air Cooled Generator for Steam Turbine", "مولد مبرد بالهواء لتوربين بخاري"),
    ("Synchronous Generator", "مولد متزامن"),
    ("AC Generator", "مولد تيار متردد"),
    ("Hydro Electric Generator", "مولد كهرومائي"),
    ("Steam Generator Exciter", "مُهيِّج مولد بخاري"),
    ("Brushless Exciter", "مُهيِّج بدون فرش"),
    ("Excitation System of Steam Turbine Generator", "نظام إثارة مولد توربين بخاري"),
    ("Excitation System of Gas Turbine Generator", "نظام إثارة مولد توربين غازي"),
    ("Excitation System of Generator", "نظام إثارة مولد"),
    ("Excitation System", "نظام الإثارة"),
    ("Static Excitation Equipment of Generator SEE", "معدات الإثارة الساكنة للمولد SEE"),
    ("Static Excitation Equipment", "معدات الإثارة الساكنة"),
    ("Thyristor - Silicon Control Rectifier", "ثايرستور - مقوم سليكوني متحكم فيه"),
    ("Collector Rings Brushes and Brush Holders Auxiliaries for Generator",
     "فرش حلقات التجميع وحوامل الفرش والملحقات للمولد"),
    ("Collector Rings Brushes", "فرش حلقات التجميع"),
    ("Insulation Resistance& Polarization Index", "مقاومة العزل ومعامل الاستقطاب"),
    ("Insulation Resistance", "مقاومة العزل"),
    ("Mechanical Parts of Generator", "الأجزاء الميكانيكية للمولد"),
    ("Neutral Generator on AC auxiliary Board", "مولد النقطة المحايدة على لوحة التيار المتردد المساعدة"),
    ("Generator", "مولد"),
    ("Generators", "المولدات"),
    ("Exciters", "المُهيِّجات"),
    ("Exciter", "مُهيِّج"),
    ("Excitation", "الإثارة"),
    ("Brushes", "فرش"),
    ("Brush", "فرشاة"),
    ("Slip Rings", "حلقات الانزلاق"),
    ("Slip Ring", "حلقة الانزلاق"),
    ("Hydrogen", "الهيدروجين"),
    # fans / filters
    ("Forced Draft Fan", "مروحة سحب قسري"),
    ("Air Force Draft Fan 2/unit", "مروحة سحب هواء قسري 2/وحدة"),
    ("Burners cooling Air Fan", "مروحة هواء تبريد الحارقات"),
    ("Fuel Gas Strainer", "مصفاة غاز الوقود"),
    ("Control Oil Pump Oil Filter", "فلتر زيت مضخة زيت التحكم"),
    ("Mazot, Light Fuel oil Screen Filter", "فلتر مصفاة المازوت وزيت الوقود الخفيف"),
    ("Gas Filter for Boiler Circulating Pump", "فلتر غاز لمضخة تدوير الغلاية"),
    ("Water Vapor Seperator", "فاصل بخار الماء"),
    ("Raw Water Clarifier, Solid Recirculation", "مروق المياه الخام، إعادة تدوير المواد الصلبة"),
    ("Gravity Filter, Sand Anthracite", "فلتر الجاذبية، رمل وأنثراسيت"),
    ("Fuel Oil Duplex Filter", "فلتر زيت وقود مزدوج"),
    ("Fuel Oil Filter", "فلتر زيت وقود"),
    ("Main Lube Oil Filter Hilco Oil Filter", "فلتر زيت التزييت الرئيسي Hilco"),
    ("Main Lube Oil Filter", "فلتر زيت التزييت الرئيسي"),
    ("Primary Air Filter Farr (30/30) and Secondary Air Filter Farr HP-100",
     "فلتر الهواء الأولي Farr (30/30) وفلتر الهواء الثانوي Farr HP-100"),
    ("Primary Air Filter", "فلتر الهواء الأولي"),
    ("Secondary Air Filter", "فلتر الهواء الثانوي"),
    ("Air Filters for Gas Turbine Frames Ms 5001P", "فلاتر هواء لإطارات التوربينات الغازية Ms 5001P"),
    ("Air Filters Duracel XL 60", "فلاتر هواء Duracel XL 60"),
    ("Air Filters", "فلاتر هواء"),
    ("Air Filter", "فلتر هواء"),
    ("Dynapure Oil Mist Collector", "مجمع رذاذ الزيت Dynapure"),
    ("Fine Oil Twin Filter", "فلتر زيت دقيق مزدوج"),
    ("Power Oil Filter, Boll.Twin Filter", "فلتر زيت القدرة، فلتر Boll المزدوج"),
    ("Power Oil Filter", "فلتر زيت القدرة"),
    ("Filter for Leakage Air", "فلتر هواء التسرب"),
    ("Fine Drier", "مجفف دقيق"),
    ("Gas Filter", "فلتر غاز"),
    ("Strainer (Gas Fuel System)", "مصفاة (نظام وقود الغاز)"),
    ("Pressure Filter, Return Filter, Tank, Fluid & Cooler", "فلتر ضغط، فلتر رجوع، خزان، سائل ومبرد"),
    ("Turbine Main Lube Oil System, Oil Tank, Oil Filters & Oil Coolers",
     "نظام زيت التزييت الرئيسي للتوربين، خزان زيت، فلاتر زيت ومبردات زيت"),
    ("Fuel Gas", "غاز الوقود"),
    ("Raw Water", "المياه الخام"),
    ("Service Water", "مياه الخدمة"),
    ("Cooling Water", "مياه التبريد"),
    ("Feed Water", "مياه التغذية"),
    ("Main Cooling Water", "مياه التبريد الرئيسية"),
    ("Desalination Water", "مياه التحلية"),
    ("Drinking Water", "مياه الشرب"),
    ("Clear Water", "مياه نظيفة"),
    ("Lubricating Water", "مياه التزييت"),
    ("Condensate Water", "مياه المكثفات"),
    ("Filtering Water", "مياه الترشيح"),
    ("Circulate Water", "مياه التدوير"),
    ("Make Up Water", "مياه تعويضية"),
    ("Fuel Oil", "زيت الوقود"),
    ("Lube Oil", "زيت التزييت"),
    ("Main Lube Oil", "زيت التزييت الرئيسي"),
    ("Control Oil", "زيت التحكم"),
    ("Power Oil", "زيت القدرة"),
    ("Fine Oil", "زيت دقيق"),
    ("Leakage Oil", "زيت التسرب"),
    ("Gas Turbine", "التوربين الغازي"),
    ("Steam Turbine", "توربين بخاري"),
    ("Steam", "بخار"),
    ("Water", "مياه"),
    ("Oil", "زيت"),
    ("Air", "هواء"),
    ("Gas", "غاز"),
    ("Fuel", "وقود"),
    ("Boilers", "الغلايات"),
    ("Boiler", "الغلاية"),
    ("Turbines", "التوربينات"),
    ("Turbine", "التوربينات"),
    ("Pumps", "المضخات"),
    ("Pump", "مضخة"),
    ("Fans", "المراوح"),
    ("Fan", "مروحة"),
    ("Filters", "المرشحات"),
    ("Filter", "فلتر"),
    ("Valves", "الصمامات"),
    ("Valve", "صمام"),
    ("Motors", "المحركات"),
    ("Motor", "محرك"),
    ("Strainer", "مصفاة"),
    ("Clarifier", "مروق"),
    ("Separator", "فاصل"),
    ("Seperator", "فاصل"),
    ("Cooler", "مبرد"),
    ("Coolers", "مبردات"),
    ("Heater", "سخان"),
    ("Tank", "خزان"),
    ("Fluid", "سائل"),
    ("Main", "الرئيسي"),
    ("Low", "منخفض"),
    # intervals / phrases with regex handled in code
]

# Phrases to protect from the generic single-word rules (keep Latin exactly).
PROTECT = ["High Dam", "IMO Pump Devision", "Pump Enbau", "Graham Pump",
           "Torshima Pump", "Demiatta PS", "Abu Sultan PS", "Talkha 2x210",
           "Talkha GT", "Talkha CC", "Sidi Krir", "Kafr El-Dawar",
           "El-Arish PS", "Ayoun Mousa PS", "Ayoun mousa", "Wadi Hof PS",
           "Al Shabab GT", "Damanhour PS", "Ayon Musa PS", "Ayon Musa",
           "Demiatta", "Abu Sultan", "Talkha", "Sidi Krir", "Kafr El-Dawar",
           "El-Arish", "Ayoun Mousa", "Wadi Hof", "Al Shabab", "Damanhour",
           "Ayon Mousa"]

# Hand translations for the two procedures: section index -> translated text
# (for list sections, the value is a list of translated items).
HAND = {
"gen-docs-app-gen-hyd-ep-all-docs-pumps-p-000-temp-r0-htm": {
 0: "محطة القوى", 1: "الإجراء الفني", 2: "المعدة: مضخة طرد مركزي",
 3: "Ugoslaf Pump", 4: "مقدمة",
 5: "يوضح هذا المستند فحص المعدة I1، والذي يجب تنفيذه كل ستة أشهر كما هو موضح بـ M6 في خانة العنوان",
 6: "المواصفات الفنية للمضخة",
 7: "Q = 1000 م3/ساعة H = 100 م P = 400 ك.و. V = 6000 فولت",
 8: "أعد المسودة الأولى م. حاتم عبد الدايم واختبرها م. هناي فهمي مدني بتاريخ 13-7-2004 في محطة السد العالي الهيدروليكية.",
 9: "احتياطات السلامة",
 10: ["يجب إصدار تصريح عمل ويجب أن يحمل فريق الصيانة المؤهل فئة السلامة المناسبة",
      "يلزم وجود سياج أمان بعلامات تحذيرية حول منطقة العمل",
      "أوقف المضخة وافصل مصدر الطاقة",
      "أغلق صمامات الخروج والدخول",
      "ضع لوحات تحذيرية مناسبة"],
 11: "العدد والأدوات والأجهزة المستخدمة",
 12: "خوذة أمان وحذاء أمان", 13: "طقم مفاتيح ربط",
 14: "معدات الضبط المحوري", 15: "شحم للتشحيم", 16: "مواد تنظيف",
 17: ["خوذة أمان وحذاء أمان", "طقم مفاتيح ربط", "معدات الضبط المحوري",
      "شحم للتشحيم", "مواد تنظيف"],
 18: "الأعمال المطلوب تنفيذها",
 19: "افحص حشوة جلاند المضخة وأضف إليها أو غيّرها",
 20: "افحص حشوة جلاند صمامات الخروج والدخول وأضف إليها أو غيّرها",
 21: "افحص مسامير المضخة والمحرك",
 22: "افحص الضبط المحوري للمضخة",
 23: ["افحص حشوة جلاند المضخة وأضف إليها أو غيّرها",
      "افحص حشوة جلاند صمامات الخروج والدخول وأضف إليها أو غيّرها",
      "افحص مسامير المضخة والمحرك", "افحص الضبط المحوري للمضخة",
      "شغّل المضخة وافحص الضوضاء والمحامل", "افحص التيار"],
 24: "الموقع: تسمية المعدة: تم الفحص بواسطة: التوقيع: تاريخ الاختبار:",
},
"gen-docs-app-gen-mdepc-pumps-p-316-r0-htm": {
 0: "محطات القوى", 1: "الإجراء الفني", 2: "المعدة: مضخة ري",
 3: "الحالة: معتمد", 4: "تاريخ الاعتماد: 14 مايو 2009",
 5: "تاريخ المراجعة التالية: مايو 2009", 6: "مقدمة",
 7: "تُستخدم هذه المضخة لتصريف المياه العادمة بعد المعالجة خارج المحطة إلى نهر النيل.",
 8: "يوضح هذا المستند قائمة فحص المعدة I1، والتي يجب تنفيذها كل شهر كما هو موضح بـ M1 في خانة العنوان أعلاه.",
 9: "أعد المسودة الأولى م. شادي غازي واختبرها مدير الصيانة",
 10: "م. أحمد شنابة وراجعها مدير عام الصيانة: م. عمران عبد الحميد شعيب واعتمدها م. أحمد ساوان رئيس قطاع محطة النوبارية وراجعها م. عبودة البنا لمراقبة الجودة بشركة MDEPC، وصدّق عليها م. سمير عبد الجليل مدير عام التفتيش ومراقبة الجودة، واعتمدها منسق MPIS م. محمد نجيب رئيس قطاع التفتيش ومراقبة الجودة",
 11: "المواصفات الفنية", 12: "احتياطات السلامة",
 13: ["يجب إصدار تصريح عمل ويجب أن يحمل فريق الصيانة المؤهل فئة السلامة المناسبة",
      "يلزم وجود سياج أمان بعلامات تحذيرية حول منطقة العمل",
      "ارتدِ معدات السلامة والصحة مثل خوذة الأمان وحذاء الأمان وقناع التنفس ... إلخ",
      "اعزل قاطع دائرة محرك المضخة",
      "افصل الأطراف الكهربائية لمحرك المضخة",
      "يجب عزل المضخة ميكانيكياً بإغلاق صمامات الطرد والسحب"],
 14: "العدد والأدوات والأجهزة المستخدمة",
 15: ["طقم أدوات صيانة كامل.", "مسطرة قياس، خرق، سائل تنظيف"],
 16: "الأعمال المطلوب تنفيذها", 17: "المضخة أثناء التشغيل",
 18: ["قِس مستوى الاهتزازات للمحامل.", "افحص كمية التصريف والضغط.",
      "افحص أي تسرب من المضخة وفلانجات المواسير", "قياس درجة حرارة المحامل",
      "افحص الجلاندات بحثاً عن تسرب"],
 19: "المضخة خارج التشغيل",
 20: ["افحص تشحيم بيت المحامل",
      "افحص جسم المضخة بحثاً عن الصدأ وأعد طلاءه (إذا لزم الأمر).",
      "افحص تثبيت المسامير ثم أعد إحكام ربطها (إذا لزم الأمر).",
      "نظف الجزء الخارجي بالهواء المضغوط",
      "اضبط الجلاندات بحثاً عن تسرب ثم أعد حشوها (إذا لزم الأمر)."],
 21: "بدء تشغيل المضخة",
 22: "قبل بدء تشغيل المضخة، يجب التحقق من الخطوات التالية",
 23: ["افتح صمامات السحب والطرد للمضخة.", "وصّل الطرف الكهربائي لمحرك المضخة.",
      "افحص اتجاه الدوران."],
 24: "الحضور والفحص أثناء التشغيل",
 25: ["افحص درجة حرارة المحامل", "افحص اهتزاز المضخة", "افحص كمية التصريف والضغط"],
 26: "الموقع: كود النظام: تاريخ آخر اختبار: تم الفحص بواسطة: التوقيع: تاريخ الاختبار:",
},
}

TITLES = {
 "gen-docs-app-gen-hyd-ep-all-docs-pumps-p-000-temp-r0-htm": "P-000-temp-r0",
 "gen-docs-app-gen-mdepc-pumps-p-316-r0-htm": "P-316-r0 \nمعتمد",
 "gen-docs-pumps-docs-page-htm": "صفحة مستندات المضخات",
 "gen-docs-generators-page-htm": "صفحة مستندات المولدات",
 "gen-docs-fans-docs-page-htm": "صفحة مستندات المراوح",
 "gen-docs-filters-docs-page-htm": "صفحة مستندات المرشحات",
}

UNCERTAIN = {
 "gen-docs-app-gen-hyd-ep-all-docs-pumps-p-000-temp-r0-htm": [
  {"term": "Ugoslaf", "context": "Equipment: Ugoslaf Pump",
   "note": "Source spelling; presumably Yugoslav. Kept in Latin."},
  {"term": "ads or change", "context": "Check the packing of the gland of the pump ads or change",
   "note": "Source reads 'ads'; rendered as 'add' (أضف إليها أو غيّرها)."},
  {"term": "noice", "context": "Operate the pump and check the noice and bearing",
   "note": "Source typo for 'noise'; rendered as الضوضاء."},
  {"term": "out let", "context": "Close the out let and inlet valves",
   "note": "Source splits 'outlet'; rendered as الخروج."},
 ],
 "gen-docs-app-gen-mdepc-pumps-p-316-r0-htm": [
  {"term": "Nubria", "context": "Eng. Ahmed Sawan Nubria power station head sector",
   "note": "Read as Nubaria power station (النوبارية)."},
  {"term": "shanabe", "context": "Eng. Ahmad shanabe",
   "note": "Transliteration of the name (شنابة) — spelling not verified."},
 ],
 "gen-docs-pumps-docs-page-htm": [
  {"term": "Draf docs", "context": "Navigation bar",
   "note": "Source spelling of 'Draft docs'; rendered مسودات المستندات."},
  {"term": "Ad docs", "context": "Navigation bar",
   "note": "Read as approved documents (المستندات المعتمدة); could also mean admin documents."},
  {"term": "Jocky Pump", "context": "Vertical Centrifugal Pump for Fire Fighting System Jocky Pump",
   "note": "Source spelling; presumably Jockey pump. Rendered مضخة جوكي."},
  {"term": "ISPAN", "context": "Back wash ver. centrifugal pump, BOMBASITUR, ISPAN",
   "note": "Source spelling (Spain); kept in Latin."},
  {"term": "Fulid", "context": "Fire Pump ITT Fulid Technology Corporation",
   "note": "Source typo for Fluid in the company name; kept in Latin."},
  {"term": "Backle / Balckle", "context": "PRa 1200/12, Backle Durr Fruntenthal / Balckle Durr Fruntenthal",
   "note": "Manufacturer name spelled two ways in the source; kept in Latin."},
  {"term": "Bofflo", "context": "Vertical SubMerged Lube Oil single stage, Centrifugal Pumps Bofflo Co",
   "note": "Source typo for Buffalo (Buffalo Forge); kept in Latin."},
 ],
 "gen-docs-generators-page-htm": [
  {"term": "Draf docs / Ad docs", "context": "Navigation bar",
   "note": "As in pumps index page; rendered مسودات المستندات / المستندات المعتمدة."},
  {"term": "EOH", "context": "Static Excitation Equipment of Generator SEE, Alstom, every 8300 EOH",
   "note": "Equivalent operating hours; rendered ساعة تشغيل مكافئة."},
  {"term": "Soduim Hypochlorite / Hypochorite", "context": "Soduim Hypochlorite Production Unit (SHPU-001) / Soduim Hypochorite Production Unit (SHPU-002)",
   "note": "Source spells Sodium as 'Soduim' and spells Hypochlorite two ways (with and without 'l'); rendered هيبوكلوريت الصوديوم in both rows."},
  {"term": "1000A of GT Siemens 1000A", "context": "G-044-r0a row",
   "note": "Garbled in the source; rendered 1000A للتوربين الغازي Siemens 1000A."},
 ],
 "gen-docs-fans-docs-page-htm": [
  {"term": "Draf docs / Ad docs", "context": "Navigation bar",
   "note": "As in pumps index page."},
 ],
 "gen-docs-filters-docs-page-htm": [
  {"term": "Draf docs / Ad docs", "context": "Navigation bar",
   "note": "As in pumps index page."},
  {"term": "Seperator", "context": "Water Vapor Seperator, RIFOX, Bremen",
   "note": "Source typo for Separator; rendered فاصل بخار الماء."},
  {"term": "depond on dp", "context": "Mazot, Light Fuel oil Screen Filter, Plenty Group Inc depond on dp",
   "note": "Source reads 'depond'; rendered حسب dp (presumably 'depend on ΔP')."},
  {"term": "Aq", "context": "when ΔP=26 Aq for Pre-filter & 38 Aq for Cubic filter",
   "note": "Kept as-is; presumably mm Aq (water column)."},
 ],
}

# ---------------------------------------------------------------- engine
def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip()

def apply_glossary(text):
    s = norm(text)
    if not s:
        return s
    # protect phrases that must stay Latin exactly
    saved = {}
    for i, p in enumerate(sorted(PROTECT, key=len, reverse=True)):
        if p in s:
            tok = f"\x00P{i}\x00"
            saved[tok] = p
            s = s.replace(p, tok)
    # interval phrases
    s = re.sub(r"Every\s+(\d+)\s+WH", r"كل \1 ساعة تشغيل", s, flags=re.I)
    s = re.sub(r"Every\s+(\d+)\s+operation hours", r"كل \1 ساعة تشغيل", s, flags=re.I)
    s = re.sub(r"every\s+(\d+)\s+EOH", r"كل \1 ساعة تشغيل مكافئة", s, flags=re.I)
    s = re.sub(r"Y1 or during stoppage", "Y1 أو أثناء التوقف", s, flags=re.I)
    s = re.sub(r"Y1 or during outage", "Y1 أو أثناء انقطاع التشغيل", s, flags=re.I)
    s = re.sub(r"when\s+ΔP=(\d+)\s*Aq for Pre-filter & (\d+) Aq for Cubic filter",
               r"عند ΔP=\1 Aq للفلتر الأولي و\2 Aq للفلتر المكعب", s, flags=re.I)
    s = re.sub(r"depending on\s+ΔP", "حسب ΔP", s, flags=re.I)
    s = re.sub(r"depond on dp", "حسب dp", s, flags=re.I)
    s = re.sub(r"depending on dp", "حسب dp", s, flags=re.I)
    s = re.sub(r"Δ>4\.2 mm water gauge", "Δ>4.2 مم عمود ماء", s)
    s = re.sub(r"ΔP=0\.6 bar", "ΔP=0.6 بار", s)
    s = re.sub(r"Pre-filter", "الفلتر الأولي", s)
    s = re.sub(r"Cubic filter", "الفلتر المكعب", s)
    # glossary, longest first
    for en, ar in sorted(GLOSSARY, key=lambda p: -len(p[0])):
        if len(en.split()) > 1 or len(en) > 6:
            s = re.sub(re.escape(en), ar, s, flags=re.I)
        else:
            s = re.sub(r"\b" + re.escape(en) + r"\b", ar, s, flags=re.I)
    for tok, p in saved.items():
        s = s.replace(tok, p)
    return re.sub(r"\s+", " ", s).strip()

def translate_section(sec):
    t = sec["type"]
    out = dict(sec)
    if t in ("paragraph", "heading"):
        out["text"] = apply_glossary(sec.get("text", ""))
    elif t == "list":
        out["items"] = [apply_glossary(i) for i in sec.get("items", [])]
    elif t == "table":
        out["rows"] = [[apply_glossary(c) for c in row] for row in sec.get("rows", [])]
    return out

def build_text_target(sections):
    """Same join rule as the source 'text' field: paragraphs/headings and
    list items joined by newlines; tables contribute nothing."""
    parts = []
    for s in sections:
        if s["type"] in ("paragraph", "heading"):
            if s.get("text"):
                parts.append(s["text"])
        elif s["type"] == "list":
            parts.extend(i for i in s.get("items", []) if i)
    return "\n".join(parts)

def check_text_rule(doc):
    """Does the join rule reproduce the source flat text (whitespace-normalised)?"""
    built = build_text_target(doc["sections"])
    a = re.sub(r"\s+", " ", built).strip()
    b = re.sub(r"\s+", " ", doc.get("text", "")).strip()
    return a == b, len(a), len(b)

IDS = [
 ("gen-docs-app-gen-hyd-ep-all-docs-pumps-p-000-temp-r0-htm", "pumps"),
 ("gen-docs-app-gen-mdepc-pumps-p-316-r0-htm", "pumps"),
 ("gen-docs-pumps-docs-page-htm", "pumps"),
 ("gen-docs-generators-page-htm", "generators"),
 ("gen-docs-fans-docs-page-htm", "fans"),
 ("gen-docs-filters-docs-page-htm", "filters"),
]

def main():
    total_words = 0
    for doc_id, cat in IDS:
        doc = json.load(open(os.path.join(ROOT, "content", doc_id + ".json"), encoding="utf-8"))
        src_words = len(doc.get("text", "").split())
        total_words += src_words
        ok, la, lb = check_text_rule(doc)
        print(f"{doc_id}: text-rule match={ok} built={la} source={lb}")
        if doc_id in HAND:
            hand = HAND[doc_id]
            assert len(hand) == len(doc["sections"]), (doc_id, len(hand), len(doc["sections"]))
            secs_t = []
            for idx, sec in enumerate(doc["sections"]):
                out = dict(sec)
                val = hand[idx]
                if sec["type"] == "list":
                    assert isinstance(val, list) and len(val) == len(sec["items"]), (doc_id, idx)
                    out["items"] = val
                else:
                    assert isinstance(val, str), (doc_id, idx)
                    out["text"] = val
                secs_t.append(out)
        else:
            secs_t = [translate_section(s) for s in doc["sections"]]
        text_t = build_text_target(secs_t)
        out_doc = {
            "id": doc_id,
            "doc_number": doc.get("doc_number"),
            "category": cat,
            "source_language": "en",
            "target_language": "ar",
            "title_target": TITLES[doc_id],
            "sections_target": secs_t,
            "text_target": text_t,
            "uncertain_terms": UNCERTAIN.get(doc_id, []),
            "word_count_source": src_words,
        }
        with open(os.path.join(OUT, doc_id + ".translation.json"), "w", encoding="utf-8") as f:
            json.dump(out_doc, f, ensure_ascii=False, indent=1)
        print(f"  wrote {doc_id}: {len(secs_t)} sections, {src_words} words")
    print("TOTAL source words:", total_words)
    # leftover-Latin scan on translated text (excluding tables' codes/names is
    # impossible to do perfectly; print everything for human review)
    import collections
    latin = collections.Counter()
    for doc_id, _ in IDS:
        d = json.load(open(os.path.join(OUT, doc_id + ".translation.json"), encoding="utf-8"))
        blob = json.dumps(d["sections_target"], ensure_ascii=False)
        for w in re.findall(r"[A-Za-z][A-Za-z0-9._/-]*", blob):
            latin[w] += 1
    print("LEFTOVER LATIN TOKENS:")
    for w, c in sorted(latin.items()):
        print(f"  {w}: {c}")

if __name__ == "__main__":
    main()
