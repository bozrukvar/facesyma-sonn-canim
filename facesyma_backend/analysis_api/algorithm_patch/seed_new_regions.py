"""
seed_new_regions.py
===================
jaw / cheekbone / chin koleksiyonlarını tüm dil veritabanlarına ekler.
Çalıştır: python seed_new_regions.py
"""

import os
from pymongo import MongoClient, UpdateOne

MONGO_URI = os.environ.get("MONGO_URI", "")
client = MongoClient(MONGO_URI)

# ── Türkçe veri ───────────────────────────────────────────────────────────────

TR_JAW = {
    "_id": "jaw",
    "jaw_width_golden": {
        "kararlı": [
            "Güçlü bir karakter yapısına sahipsiniz; zorluklarla başa çıkmada kararlı adımlar atarsınız.",
            "Kararlarınızda tutarlı ve güvenilirsinizdir; çevreniz bu özelliğinize güvenir.",
            "Hayatta karşılaştığınız engelleri sabırla ve kararlılıkla aşma gücüne sahipsiniz.",
            "Zor anlarda bile sağlam duruşunuzla çevrenize güç verirsiniz.",
        ],
        "güvenilir": [
            "Güvenilirliğiniz, çevrenizin size her zaman başvurmasını sağlar.",
            "Verdiğiniz sözleri yerine getirme konusunda istikrarlısınızdır.",
            "İnsanlar size kolayca güvenir; bu özellik sosyal hayatınızda büyük avantaj sağlar.",
            "Sözünüzün eri olmanız, çevrenizde derin bir saygınlık oluşturur.",
        ],
        "dengeli": [
            "Duygusal denge sizin için bir önceliktir; düşünceli kararlar alırsınız.",
            "Hayatın farklı boyutlarına dengeli bir yaklaşım sergilersiniz.",
            "Stresli anlarda dahi sakinliğinizi koruma beceriniz öne çıkar.",
            "Mantık ile duyguyu dengede tutma yeteneğiniz gelişmiştir.",
        ],
        "güçlü": [
            "İçsel gücünüz, zorluklarla karşılaştığınızda sizi ayakta tutan temel özelliğinizdir.",
            "Güçlü bir iradeye sahipsiniz; bu irade size zor anlarda yol gösterir.",
            "Fiziksel ve ruhsal dayanıklılığınız çevrenize ilham kaynağı olur.",
            "Engellerle yüzleşmekten çekinmezsiniz; bu güç kişiliğinizin özündedir.",
        ],
    },
    "jaw_wide": {
        "güçlü": [
            "Güçlü bir kişilik yapısına sahipsiniz; bu güç hem fiziksel hem de ruhsal olarak kendini gösterir.",
            "Yaşamda yer açma ve tutunma konusunda doğal bir güce sahipsiniz.",
            "Engeller karşısında eğilmez bir yapınız var; bu sizin en güçlü özelliklerinizden biridir.",
            "Kararlı duruşunuz çevrenize güven ve güç aşılar.",
        ],
        "lider": [
            "Doğal bir liderlik karizmanız var; insanlar sizin etrafınızda toplanmaktan keyif alır.",
            "Grup içinde yönlendirici rolü üstlenmek sizin için oldukça doğaldır.",
            "Liderlik vasıflarınız sizi çevrenizde öne çıkaran temel özelliklerinizden biridir.",
            "İnsanları motive etme ve bir araya getirme konusundaki yeteneğiniz dikkat çekicidir.",
        ],
        "etkileyici": [
            "Çevrenizde güçlü bir izlenim bırakırsınız; insanlar sizi kolayca unutamaz.",
            "Etkileyici varlığınız, girdiğiniz ortamda fark edilmenizi sağlar.",
            "Doğal karizmanız sayesinde insanlar üzerinde kalıcı bir etki bırakırsınız.",
            "Güçlü duruşunuz ve özgüveniniz sizi etkileyici kılar.",
        ],
        "kararlı": [
            "Kararlarınızda sarsılmaz bir kararlılık taşırsınız.",
            "Hedeflerinize ulaşma yolunda hiçbir engel sizi durduramaz.",
            "Güçlü iradeniz zorlu süreçlerde sizi ön plana çıkarır.",
            "Aldığınız kararların arkasında durmak sizin için onur meselesidir.",
        ],
        "enerjik": [
            "Yüksek enerji seviyeniz sizi çevrenizde hareketli ve dinamik kılar.",
            "Enerjinizi verimli kullanma beceriniz başarılarınızın temelini oluşturur.",
            "Dinamo gibi bir enerjiye sahipsiniz; bu enerji çevrenizi de etkiler.",
            "Hayata dolu dolu katılımınız, çevrenizi de canlandırır.",
        ],
    },
    "jaw_narrow": {
        "zarif": [
            "Zarafet sizin için sadece bir özellik değil, bir yaşam biçimidir.",
            "İnce ve zarif bir kişiliğe sahipsiniz; bu özellik çevrenizi etkiler.",
            "Her ortamda zarif ve ölçülü bir duruş sergileme yeteneğiniz vardır.",
            "Estetik anlayışınız ve zarafetle birleşince çevrenizde unutulmaz bir iz bırakırsınız.",
        ],
        "narin": [
            "Hassas ve narin bir ruh haline sahipsiniz; bu duyarlılık yaratıcılığınızı besler.",
            "İncelikli bakış açınız sizi çevrenizden ayıran temel özelliğinizdir.",
            "Narin yapınız sizi ince detaylara dikkat eden biri olarak öne çıkarır.",
            "Kırılgan görünen ama aslında derinden güçlü bir yapınız var.",
        ],
        "sanatsal": [
            "Sanatsal bir ruha sahipsiniz; güzelliği fark etme ve yaratma içgüdünüz güçlüdür.",
            "Estetik anlayışınız oldukça gelişmiştir; bu sizi sanatsal alanlarda başarılı kılar.",
            "Sanata olan ilginiz ve yaratıcılığınız hayatınızın ayrılmaz bir parçasıdır.",
            "Sanatsal duyarlılığınız çevrenize de ilham verir.",
        ],
        "yaratıcı": [
            "Yaratıcı düşünce yapınız sorunlara alışılmışın dışında çözümler üretmenizi sağlar.",
            "Hayal gücünüz geniştir; bu özellik sizi her alanda öne çıkarır.",
            "Yenilikçi bakış açınız çevrenizde fark yaratmanızı sağlar.",
            "Sıradan şeyleri olağanüstü hale getirme yeteneğiniz vardır.",
        ],
        "hassas": [
            "Çevrenizdekilerin duygularına karşı son derece duyarlısınızdır.",
            "İnce duygularınız insanlarla derin bağlar kurmanızı kolaylaştırır.",
            "Empati yeteneğiniz oldukça güçlüdür; bu sizi değerli bir dost yapar.",
            "Duygusal zekanız yüksektir; insanları anlama ve kavrama konusunda yeteneklisiniz.",
        ],
    },
}

TR_CHEEKBONE = {
    "_id": "cheekbone",
    "cheekbone_golden": {
        "çekici": [
            "Dengeli yüz hatlarınız size doğal bir çekicilik katar.",
            "Çevreniz sizi ilk bakışta etkileyici buluyor; bu doğal çekiciliğinizin yansımasıdır.",
            "Çekici görünümünüz insanlarla kolayca bağlantı kurmanızı sağlar.",
            "Doğal çekiciliğiniz kişiliğinizle bütünleşmiş gerçek bir özelliğinizdir.",
        ],
        "karizmatik": [
            "Doğal karizmanız sizi girdiğiniz her ortamda öne çıkarır.",
            "İnsanlar sizinle zaman geçirmekten keyif alır; bu karizmanızın göstergesidir.",
            "Karizmatik kişiliğiniz çevreniz üzerinde güçlü bir etki bırakır.",
            "Sadece görünüşünüzle değil, varlığınızla da etkileyicisinizdir.",
        ],
        "dengeli": [
            "Dengeli bir kişilik yapısına sahipsiniz; bu denge hayatınızın her alanına yansır.",
            "Hem sosyal hem de bireysel yaşamınızda denge kurma beceriniz gelişmiştir.",
            "Hayata dengeli yaklaşımınız çevrenize huzur verir.",
            "Aşırılıklardan kaçınır, orta yolu bulmada başarılısınızdır.",
        ],
        "etkileyici": [
            "Güçlü bir ilk izlenim bırakırsınız; insanlar sizi kolayca unutamaz.",
            "Etkileyici varlığınız sosyal ortamlarda öne çıkmanızı sağlar.",
            "Çevrenizde iz bırakan bir kişiliğe sahipsiniz.",
            "Konuştuğunuzda insanlar dikkatle dinler; bu etkileyiciliğinizin sonucudur.",
        ],
        "uyumlu": [
            "Farklı insanlarla kolayca uyum sağlayabilirsiniz; bu sosyal bir avantajdır.",
            "Uyumlu kişiliğiniz grup ortamlarında değerli bir üye olmanızı sağlar.",
            "Değişen koşullara hızla adapte olma yeteneğiniz öne çıkar.",
            "Farklı görüşlere saygıyla yaklaşmanız uyumunuzu pekiştirir.",
        ],
    },
    "cheekbone_high": {
        "çekici": [
            "Belirgin kemik yapınız size güçlü ve çekici bir görünüm kazandırır.",
            "Çekiciliğiniz hem fiziksel hem de kişilik özelliklerinizde kendini gösterir.",
            "İnsanlar sizi ilk görüşte dikkat çekici ve etkileyici buluyor.",
            "Doğal çekiciliğiniz her yaşta ve her koşulda öne çıkar.",
        ],
        "karizmatik": [
            "Güçlü karizmanız sizi toplantı ve sosyal ortamlarda doğal odak noktası yapar.",
            "İnsanlar üzerindeki etkiniz karizmanızdan kaynaklanır; bu en önemli güçlerinizden biridir.",
            "Karizmatik varlığınız liderlik rollerinde size avantaj sağlar.",
            "Söylediğiniz şeyler ağırlık taşır; bu karizmanızın gücünden gelir.",
        ],
        "sosyal": [
            "Sosyal ortamlarda kendinizi rahat hissedersiniz; insanlarla bağ kurmak sizin için doğaldır.",
            "Geniş bir sosyal çevreye sahipsiniz ve bu çevreyi genişletmek sizin için kolaydır.",
            "İnsanlarla iletişim kurma konusundaki yeteneğiniz sosyal hayatınızı zenginleştirir.",
            "Sosyal enerjiniz çevrenizdekileri de olumlu etkiler.",
        ],
        "lider": [
            "Doğal liderlik özellikleriniz sizi gruplarda yönlendirici konuma taşır.",
            "İnsanları etkileme ve yönlendirme yeteneğiniz güçlüdür.",
            "Liderlik vasfınız doğuştandır; zorlu anlarda çevreniz size bakar.",
            "Grup dinamiklerini okuma ve yönetme konusunda yeteneklisiniz.",
        ],
        "cazip": [
            "Cazip bir kişiliğe sahipsiniz; bu özellik hem sosyal hem de profesyonel hayatınıza katkı sağlar.",
            "Çevreniz sizi etkileyici ve çekici buluyor; bu doğal bir özelliğinizdir.",
            "Kişiliğinizdeki çekicilik ilişkilerinizi güçlü kılar.",
            "İlgi odağı olmak size göre bir durumdur; bunu zarafetle taşırsınız.",
        ],
    },
    "cheekbone_low": {
        "güvenilir": [
            "Samimi ve güvenilir yapınız çevrenizin size olan güvenini pekiştirir.",
            "Güvenilirliğiniz uzun süreli ilişkilerin temelini oluşturur.",
            "İnsanlar sıkıntılı anlarda size başvurur; bu güvenilirliğinizin kanıtıdır.",
            "Gösterişten uzak ama özden gelen bir güvenilirliğe sahipsiniz.",
        ],
        "dengeli": [
            "Sakin ve dengeli yapınız çevrenize huzur verir.",
            "Aşırıya kaçmayan ölçülü bir kişilik yapısına sahipsiniz.",
            "Dengeyi koruma konusundaki yeteneğiniz çevrenize örnek olur.",
            "İç dengeniz dışarıya da yansır ve etrafınızı sakinleştirir.",
        ],
        "pratik": [
            "Pratik ve gerçekçi bir bakış açısına sahipsiniz; bu özellik karar almayı kolaylaştırır.",
            "Somut çözümler üretme konusundaki yeteneğiniz öne çıkar.",
            "Hayata pragmatik yaklaşımınız sizi güvenilir bir çözüm ortağı yapar.",
            "Hayali değil, gerçek ve uygulanabilir planlar yaparsınız.",
        ],
        "dikkatli": [
            "Dikkatli ve titiz bir kişiliğe sahipsiniz; ayrıntıları gözden kaçırmazsınız.",
            "Adım atmadan önce iyice düşünme alışkanlığınız hata yapma oranınızı azaltır.",
            "Temkinli yapınız önemli kararlar alırken size büyük avantaj sağlar.",
            "Düşünmeden hareket etmezsiniz; bu temkinlilik sizi korur.",
        ],
        "uyumlu": [
            "Farklı ortam ve koşullara kolayca uyum sağlarsınız.",
            "Uyumlu ve esnek yapınız iş ve sosyal hayatınızda değerli bir özellik olarak öne çıkar.",
            "Değişime açık tutumunuz hayatta daha az dirençle ilerlemenizi sağlar.",
            "Çevrenizle sürtüşmeden akmayı başarırsınız.",
        ],
    },
}

TR_CHIN = {
    "_id": "chin",
    "chin_balanced": {
        "analitik": [
            "Analitik düşünce yapınız karmaşık sorunları sistematik biçimde çözmenizi sağlar.",
            "Olayları mantıklı ve analitik bir perspektifle değerlendirirsiniz.",
            "Veri ve gözlemlere dayalı karar almanız sizi güvenilir bir düşünür yapar.",
            "Sorunların kökenine inerek çözüm üretme konusunda yeteneklisiniz.",
        ],
        "kararlı": [
            "Dengeli yapınız kararlarınızda kararlılık ve tutarlılık sağlar.",
            "Hedeflerinize ulaşmada kendi yönteminizi izleme konusunda kararlısınızdır.",
            "Güçlü iradeniz zorlu süreçlerde sizi ön plana çıkarır.",
            "Başladığınız işi sonuna kadar götürme konusunda istikrarlısınızdır.",
        ],
        "dengeli": [
            "Hayatın farklı boyutlarına dengeli yaklaşmanız iç huzurunuzu sağlar.",
            "Mantık ve duyguyu dengede tutma becerisi sizin güçlü yanlarınızdan biridir.",
            "Dengeli kişiliğiniz hem bireysel hem de sosyal yaşamınıza olumlu yansır.",
            "Aşırılıklardan uzak duran dengeli bir yaşam anlayışınız vardır.",
        ],
        "güvenilir": [
            "İnsanlar güvenilir yapınız sayesinde size kolay güven duyar.",
            "Tutarlı ve güvenilir karakteriniz uzun süreli ilişkilerin temelini oluşturur.",
            "Verdiğiniz sözlerin arkasında durmak sizin için bir onur meselesidir.",
            "Güvenilirliğiniz sessiz ama derin bir güce sahiptir.",
        ],
        "odaklı": [
            "Hedeflerinize odaklanma ve dikkatinizi dağıtmadan ilerleme konusunda başarılısınızdır.",
            "Yaptığınız işe tam anlamıyla konsantre olursunuz; bu odaklanma başarınızın anahtarıdır.",
            "Öncelikleri belirleme ve onlara bağlı kalma yeteneğiniz güçlüdür.",
            "Dikkatinizi dağıtacak şeylere rağmen odaklanabilme yeteneğiniz öne çıkar.",
        ],
    },
    "chin_pointed": {
        "yaratıcı": [
            "Yaratıcı zihniniz sıradan durumları olağanüstü fırsatlara dönüştürme gücüne sahiptir.",
            "Özgün fikirler üretme konusunda doğal bir yeteneğiniz var.",
            "Yaratıcılığınız hayatınızın her alanında kendini gösterir.",
            "Kalıpların dışına çıkma cesaretiniz yaratıcılığınızı besler.",
        ],
        "sezgisel": [
            "Güçlü sezgileriniz doğru kararlar almanızda size rehberlik eder.",
            "Olayların arka planını hissetme yeteneğiniz oldukça gelişmiştir.",
            "Sezgilerinize güvenmek sizi çoğu zaman doğru yönde ilerletir.",
            "İçgüdüsel yönlendirmeleriniz çoğunlukla haklı çıkar.",
        ],
        "zeki": [
            "Keskin zekanız bilgileri hızla analiz etme ve işleme yeteneği verir.",
            "Zeka ve yaratıcılığı bir arada kullanan nadir kişilerden birisiniz.",
            "Sorulara hızlı ve isabetli yanıtlar bulma konusunda üstün bir yeteneğiniz var.",
            "Zeka sadece bilgi değil; sizi farklı kılan anlama ve yorumlama gücünüzdür.",
        ],
        "hassas": [
            "Çevrenize olan yüksek duyarlılığınız empati kurmanızı kolaylaştırır.",
            "Detaylara olan hassasiyetiniz özellikle yaratıcı alanlarda büyük avantaj sağlar.",
            "İnce duygularınız derin ve anlamlı ilişkiler kurmanızı mümkün kılar.",
            "Hassasiyetiniz zayıflık değil; derin anlayışınızın işaretidir.",
        ],
        "analitik": [
            "Keskin analizcilik yeteneğiniz sizi problem çözmede başarılı kılar.",
            "Olayları derinlemesine inceleme ve anlamlandırma konusunda yeteneklisiniz.",
            "Analitik bakış açınız hayatın karmaşık sorularına sistematik cevaplar bulmanızı sağlar.",
            "Gördüklerinizin ötesine geçerek derinlemesine düşünebilirsiniz.",
        ],
    },
    "chin_round": {
        "şefkatli": [
            "Şefkatli yapınız çevrenizdekilerin duygusal ihtiyaçlarına karşı sizi duyarlı kılar.",
            "Başkalarına olan ilginiz ve şefkatiniz sizi değerli bir dost yapar.",
            "İnsanlara samimi bir sıcaklık ve ilgi gösterme konusunda içgüdüsel bir yeteneğiniz var.",
            "Kalbinizin genişliği çevrenizdekilere de yansır.",
        ],
        "sosyal": [
            "İnsanlarla doğal bir uyum içinde ilişki kurarsınız; bu sosyal açıdan büyük bir güçtür.",
            "Sosyal ortamlarda kendinizi rahat hissedersiniz ve başkalarını da rahatlatırsınız.",
            "Geniş sosyal çevreniz hayatınızı zenginleştiren en önemli kaynaklardan biridir.",
            "İnsanların yanında olmaktan gerçek bir mutluluk duyarsınız.",
        ],
        "uyumlu": [
            "Farklı kişiliklerle uyum içinde çalışabilme yeteneğiniz son derece gelişmiştir.",
            "Esnek ve uyumlu yapınız grup ortamlarında sizi değerli bir üye yapar.",
            "Koşullar değişse bile uyum sağlama konusundaki doğal yeteneğiniz öne çıkar.",
            "Anlaşmazlıklarda köprü kuran biri olmaya yatkınsınızdır.",
        ],
        "cömert": [
            "Cömertliğiniz sadece maddi değil; zaman, enerji ve sevgi paylaşımında da kendini gösterir.",
            "Başkalarına yardım etmek sizin için bir yükümlülük değil, içten gelen bir istek.",
            "Cömert ruhunuz çevrenizde sizi sevilen ve aranan biri yapar.",
            "Vermenin aldığınızdan daha fazla mutluluk getirdiğini içtenlikle hissedersiniz.",
        ],
        "açık_kalpli": [
            "Açık kalplilik sizin en belirgin özelliklerinizden biridir; insanlara kolayca güvenir ve kucaklarsınız.",
            "Yargılamadan kabul etme yeteneğiniz sizi güvenilir bir sığınak haline getirir.",
            "Açık yürekli tutumunuz çevrenizde derin ve anlamlı ilişkiler kurmanızı sağlar.",
            "Kalp kapılarınız her zaman aralanmaya hazır; bu sizi nadir bir insan yapar.",
        ],
    },
}

# ── İngilizce veri ────────────────────────────────────────────────────────────

EN_JAW = {
    "_id": "jaw",
    "jaw_width_golden": {
        "determined": [
            "Your balanced jaw reflects a determined character; you face challenges with steady resolve.",
            "You approach decisions with consistency and determination that others rely on.",
            "When obstacles arise, you meet them with patient yet unwavering perseverance.",
            "Your inner resolve gives strength to those around you in difficult moments.",
        ],
        "reliable": [
            "Your reliability makes others naturally turn to you in times of need.",
            "You follow through on commitments with remarkable consistency.",
            "People trust you easily; this quality gives you a significant social advantage.",
            "Your word carries weight because you always honor it.",
        ],
        "balanced": [
            "Emotional balance is a priority for you; you make thoughtful decisions.",
            "You approach life's many dimensions with a well-calibrated perspective.",
            "Even under stress, your ability to maintain composure stands out.",
            "You balance reason and feeling in a way most people find admirable.",
        ],
        "strong": [
            "Your inner strength is the quality that keeps you standing when challenges arise.",
            "You possess a powerful will that guides you through difficult times.",
            "Your resilience — physical and emotional — inspires those around you.",
            "Strength for you is not aggression but steady, quiet endurance.",
        ],
    },
    "jaw_wide": {
        "strong": [
            "You have a powerful personality; this strength shows both physically and in character.",
            "You possess a natural force for carving out your place and holding it in the world.",
            "You have an unbending quality in the face of obstacles — one of your most defining traits.",
            "Your firm stance instills confidence and strength in those around you.",
        ],
        "leader": [
            "You have a natural leadership charisma; people enjoy gathering around you.",
            "Taking a guiding role within a group comes very naturally to you.",
            "Your leadership qualities are among the traits that distinguish you from the crowd.",
            "Motivating and uniting people is something you do instinctively.",
        ],
        "impressive": [
            "You leave a strong impression on those around you; people cannot easily forget you.",
            "Your commanding presence ensures you stand out in any environment.",
            "Thanks to your natural charisma, you leave a lasting mark on people.",
            "Your confidence and bearing make you genuinely impressive.",
        ],
        "determined": [
            "You carry unwavering determination in your decisions.",
            "Nothing on the road to your goals can stop you.",
            "Your strong will puts you at the forefront in demanding situations.",
            "Standing behind the choices you make is a matter of personal honor for you.",
        ],
        "energetic": [
            "Your high energy level makes you a dynamic and vital force in your environment.",
            "Your skill in channeling energy productively is the foundation of your success.",
            "You have a dynamo-like energy that uplifts everyone around you.",
            "Your full engagement with life energizes those who share it with you.",
        ],
    },
    "jaw_narrow": {
        "delicate": [
            "Elegance for you is not merely a trait — it is a way of living.",
            "You have a refined and delicate personality that leaves a subtle impression on others.",
            "You have the ability to carry yourself with grace and restraint in every setting.",
            "You appear fragile on the surface yet harbor a quiet, deep strength within.",
        ],
        "artistic": [
            "You have an artistic soul; your instinct for perceiving and creating beauty is strong.",
            "Your aesthetic sensibility is highly developed, making you successful in creative fields.",
            "Your passion for art and your creativity are inseparable parts of who you are.",
            "Your artistic sensitivity is a source of inspiration for those around you.",
        ],
        "creative": [
            "Your creative mind has the power to transform ordinary situations into extraordinary ones.",
            "You have a natural talent for generating original ideas.",
            "Your creative thinking shows itself in every area of your life.",
            "You have the ability to make the ordinary extraordinary.",
        ],
        "sensitive": [
            "You are extraordinarily attuned to the feelings of those around you.",
            "Your fine emotional sensibility makes it easy to form deep connections with others.",
            "Your empathy is genuinely strong — it makes you a treasured friend.",
            "Your sensitivity is not a weakness; it is the mark of your profound understanding.",
        ],
        "intuitive": [
            "Your strong intuitions guide you toward making the right choices.",
            "Your ability to sense what lies beneath the surface is exceptionally well developed.",
            "Trusting your instincts most often steers you in the right direction.",
            "Your gut feelings tend to prove correct more often than not.",
        ],
    },
}

EN_CHEEKBONE = {
    "_id": "cheekbone",
    "cheekbone_golden": {
        "attractive": [
            "Your balanced facial structure lends you a natural attractiveness.",
            "Those around you find you striking at first glance — a reflection of your natural appeal.",
            "Your attractive appearance makes it easy for you to connect with others.",
            "Your natural allure is a genuine part of who you are, fully integrated with your character.",
        ],
        "charismatic": [
            "Your natural charisma puts you at the center of attention in any room you enter.",
            "People genuinely enjoy spending time with you — a testament to your charisma.",
            "Your charismatic personality leaves a powerful impression on those around you.",
            "You are captivating not just in appearance but in presence.",
        ],
        "balanced": [
            "You have a balanced personality; this equilibrium resonates through every area of your life.",
            "Your ability to maintain balance in both your social and personal life is well developed.",
            "Your balanced approach to life brings calm and stability to those around you.",
            "You avoid extremes and possess a talent for finding the middle path.",
        ],
        "impressive": [
            "You leave a strong first impression; people do not easily forget you.",
            "Your impressive presence ensures you stand out in social settings.",
            "You have a personality that leaves a mark on every environment you enter.",
            "When you speak, people listen — this is the power of your impressiveness.",
        ],
        "harmonious": [
            "You can easily get along with very different kinds of people — a genuine social advantage.",
            "Your harmonious personality makes you a valued member of any group.",
            "Your ability to adapt quickly to changing circumstances is a defining quality.",
            "You know how to respect different perspectives, which reinforces your harmony with others.",
        ],
    },
    "cheekbone_high": {
        "attractive": [
            "Your prominent bone structure lends you a strong and striking appearance.",
            "Your attractiveness shows itself both physically and in the depth of your personality.",
            "People find you striking and impressive from the very first moment.",
            "Your natural appeal stands out at every age and in every circumstance.",
        ],
        "charismatic": [
            "Your powerful charisma makes you the natural center of focus in meetings and social gatherings.",
            "Your influence over others stems from your charisma — one of your most important strengths.",
            "Your charismatic presence gives you a distinct advantage in leadership roles.",
            "What you say carries weight; this power comes from your charisma.",
        ],
        "social": [
            "You feel at ease in social settings; forming connections with people comes naturally to you.",
            "You have a wide social circle, and expanding it requires little effort on your part.",
            "Your talent for communication enriches your social life in meaningful ways.",
            "Your social energy has a positive effect on those who share space with you.",
        ],
        "leader": [
            "Your innate leadership qualities propel you into guiding roles within groups.",
            "Your ability to influence and direct others is genuinely strong.",
            "Your leadership is innate — when things get hard, those around you look to you.",
            "Reading and managing group dynamics is something you do with natural ease.",
        ],
        "confident": [
            "You carry a quiet confidence that others immediately sense and respect.",
            "Self-assurance flows through everything you do, setting you apart.",
            "Your confidence is not arrogance — it is grounded self-knowledge.",
            "Being the center of attention suits you; you carry it with grace.",
        ],
    },
    "cheekbone_low": {
        "reliable": [
            "Your genuine and trustworthy nature strengthens the confidence others place in you.",
            "Your reliability forms the foundation of lasting relationships.",
            "People seek you out in difficult moments — proof of your trustworthiness.",
            "Your reliability is unflashy but rooted in something real and deep.",
        ],
        "balanced": [
            "Your calm and balanced nature brings peace to those around you.",
            "You have a measured personality that avoids going to extremes.",
            "Your ability to maintain equilibrium sets an example for others.",
            "Your inner balance radiates outward, steadying those around you.",
        ],
        "practical": [
            "You have a pragmatic, realistic worldview that makes decision-making easier.",
            "Your ability to produce concrete, workable solutions is a standout quality.",
            "Your practical approach to life makes you a dependable problem-solving partner.",
            "You make plans that are real and achievable, not merely idealistic.",
        ],
        "thorough": [
            "You are careful and meticulous by nature; details do not escape your attention.",
            "Your habit of thinking things through before acting reduces your rate of error.",
            "Your cautious temperament gives you a major advantage when making important decisions.",
            "You don't act without thinking — this care protects you time and again.",
        ],
        "harmonious": [
            "You adapt easily to different environments and conditions.",
            "Your flexible and harmonious nature stands out as a valuable asset in work and social life.",
            "Your openness to change allows you to move through life with less resistance.",
            "You have a gift for going with the flow without losing yourself.",
        ],
    },
}

EN_CHIN = {
    "_id": "chin",
    "chin_balanced": {
        "analytical": [
            "Your analytical mind enables you to resolve complex problems in a systematic way.",
            "You evaluate events through a logical and analytical perspective.",
            "Making decisions based on data and observation makes you a trustworthy thinker.",
            "You are skilled at getting to the root of problems and generating solutions.",
        ],
        "determined": [
            "Your balanced nature produces determination and consistency in your decisions.",
            "You are resolute in pursuing your goals in your own way.",
            "Your strong will puts you at the forefront in demanding situations.",
            "You carry an undertaking through to the end with remarkable steadiness.",
        ],
        "balanced": [
            "Approaching life's many dimensions with balance brings you inner peace.",
            "Your ability to hold reason and emotion in equilibrium is one of your true strengths.",
            "Your balanced personality shows up positively in both your personal and social life.",
            "You embrace a way of living that avoids extremes and cultivates stability.",
        ],
        "reliable": [
            "People place their trust in you naturally, thanks to your dependable character.",
            "Your consistent and trustworthy character forms the foundation of lasting relationships.",
            "Standing behind the decisions you make is a matter of personal honor for you.",
            "Your reliability is quiet but carries a deep and lasting power.",
        ],
        "focused": [
            "You excel at staying focused on your goals without letting your attention drift.",
            "You concentrate fully on what you do; this focus is the key to your success.",
            "Your capacity to set priorities and remain committed to them is well developed.",
            "Even surrounded by distractions, your ability to stay on task stands out.",
        ],
    },
    "chin_pointed": {
        "creative": [
            "Your creative mind holds the power to turn ordinary situations into extraordinary ones.",
            "You have a natural talent for generating original ideas.",
            "Your creativity shows itself in every area of your life.",
            "The courage to step outside established patterns feeds your creativity.",
        ],
        "intuitive": [
            "Your strong intuitions guide you toward making the right choices.",
            "Your ability to sense what lies beneath the surface is exceptionally well developed.",
            "Trusting your instincts most often steers you in the right direction.",
            "Your gut feelings prove correct more often than most people's careful analysis.",
        ],
        "intelligent": [
            "Your sharp intelligence gives you the ability to rapidly analyze and process information.",
            "You are among those rare people who combine intellect and creativity.",
            "You possess a remarkable ability to find quick, accurate answers to complex questions.",
            "Intelligence, for you, is not just knowledge — it is the power to understand and interpret.",
        ],
        "sensitive": [
            "Your heightened sensitivity to your surroundings makes empathy come naturally.",
            "Your attention to fine details is a major advantage, especially in creative fields.",
            "Your subtle emotional perceptiveness makes it possible to form deep, meaningful connections.",
            "Your sensitivity is not weakness — it is the signature of your deep understanding.",
        ],
        "analytical": [
            "Your sharp analytical ability makes you effective at solving problems.",
            "You have a talent for examining events deeply and drawing meaning from them.",
            "Your analytical perspective helps you find systematic answers to life's complex questions.",
            "You have the capacity to think beyond what you see and reason at a deeper level.",
        ],
    },
    "chin_round": {
        "compassionate": [
            "Your compassionate nature makes you deeply attuned to the emotional needs of those around you.",
            "Your care and warmth for others make you a genuinely treasured friend.",
            "You have an instinctive talent for showing authentic warmth and interest to people.",
            "The breadth of your heart is felt by everyone who spends time with you.",
        ],
        "social": [
            "You form connections with others in a naturally harmonious way — a true social strength.",
            "You feel at ease in social settings and you put others at ease too.",
            "Your wide social circle is one of the most enriching sources in your life.",
            "You find genuine happiness in simply being with other people.",
        ],
        "harmonious": [
            "Your ability to work in harmony with very different kinds of personalities is highly developed.",
            "Your flexible and harmonious nature makes you a valued member of any group.",
            "Even as circumstances shift, your natural talent for adaptation continues to stand out.",
            "You have a gift for being a bridge-builder in times of disagreement.",
        ],
        "generous": [
            "Your generosity shows not only in material giving but in sharing time, energy, and love.",
            "Helping others is not an obligation for you — it is a heartfelt desire.",
            "Your generous spirit makes you one of the most loved and sought-after people in any circle.",
            "You genuinely feel that giving brings you more happiness than receiving.",
        ],
        "open_hearted": [
            "Open-heartedness is one of your most defining traits; you trust and embrace people with ease.",
            "Your ability to accept without judgment makes you a safe haven for others.",
            "Your open, warm attitude allows you to build deep, meaningful relationships.",
            "Your heart's doors are always ready to be opened — this makes you a rare human being.",
        ],
    },
}

# ── Ekleme fonksiyonu ─────────────────────────────────────────────────────────

def seed_language(db_name, jaw_doc, cheekbone_doc, chin_doc):
    db = client[db_name]
    for col_name, doc in [("jaw", jaw_doc), ("cheekbone", cheekbone_doc), ("chin", chin_doc)]:
        result = db[col_name].replace_one({"_id": doc["_id"]}, doc, upsert=True)
        print(f"  [{db_name}] {col_name}: upserted={result.upserted_id is not None}, matched={result.matched_count}")


print("Seeding Turkish databases...")
for db_name in ["database_attribute_tr"]:
    seed_language(db_name, TR_JAW, TR_CHEEKBONE, TR_CHIN)

print("Seeding English databases...")
for db_name in ["database_attribute_en"]:
    seed_language(db_name, EN_JAW, EN_CHEEKBONE, EN_CHIN)

# Other 6 existing languages — use EN data
print("Seeding other existing language databases (EN base)...")
for db_name in ["database_attribute_de", "database_attribute_ru", "database_attribute_ar",
                "database_attribute_sp", "database_attribute_kr", "database_attribute_jp"]:
    seed_language(db_name, EN_JAW, EN_CHEEKBONE, EN_CHIN)

# 10 new language databases — use EN data
print("Seeding new language databases (EN base)...")
for db_name in ["database_attribute_bn", "database_attribute_fr", "database_attribute_hi",
                "database_attribute_id", "database_attribute_it", "database_attribute_pl",
                "database_attribute_pt", "database_attribute_ur", "database_attribute_vi",
                "database_attribute_zh"]:
    seed_language(db_name, EN_JAW, EN_CHEEKBONE, EN_CHIN)

print("Done.")
client.close()
