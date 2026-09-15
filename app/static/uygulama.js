/* ZÎC · uygulama betiği
   index.html'den ayrıldı. Bir işlevi değiştirmeden önce burada
   ARAYIN: aynı adla ikinci bir tanım varsa ikincisi kazanır ve
   sessizce ötekini ezer. Bu daha önce üç kez oldu. */
const TZLER=["Europe/Istanbul","Europe/Berlin","Europe/London","Europe/Paris",
"Europe/Amsterdam","Europe/Vienna","Europe/Moscow","Europe/Athens","Europe/Sofia",
"Asia/Baku","Asia/Tbilisi","Asia/Tehran","Asia/Baghdad","Asia/Riyadh","Asia/Dubai",
"Africa/Cairo","America/New_York","America/Chicago","America/Los_Angeles","UTC"];

const $=id=>document.getElementById(id);

/* ERİŞİM ANAHTARI — kritik düzeltme.
   Site anahtarı açıkken sayfaya ?anahtar=... ile giriliyor, ama tarayıcı bu
   sorgu dizgesini sonraki fetch çağrılarına TAŞIMAZ. Bu yüzden yerler,
   rol-bilgi, tz-check ve analiz istekleri 401 alıyor; il/ilçe listesi boş
   kalıyordu. Anahtar bir kez okunup her isteğe başlık olarak ekleniyor. */
const ZIC_ANAHTAR=(new URLSearchParams(location.search)).get("anahtar")||"";
/* Uzun süren AI çağrılarında tarayıcı "Failed to fetch" veriyordu: sunucu
   hâlâ çalışırken aradaki vekil bağlantıyı kesiyor. Artık istek kendi
   zaman aşımıyla iptal ediliyor ve bir kez otomatik tekrarlanıyor —
   kullanıcı ham ağ hatası görmüyor. */
const ZIC_ZAMAN_ASIMI=95000;
(function(){
  const asil=window.fetch;
  window.fetch=function(kaynak,ayar){
    ayar=ayar||{};
    if(ZIC_ANAHTAR && typeof kaynak==="string" && kaynak.startsWith("/")){
      ayar.headers=Object.assign({},ayar.headers,{"x-zic-anahtar":ZIC_ANAHTAR});
    }
    // AI uçları uzun sürer; ötekiler kısa. İkisine de tavan koy.
    if(!ayar.signal){
      const kt=new AbortController();
      // AI ve ağır hesap uçlarının hepsi uzun sürebilir. Liste eksik kalınca
      // yeni uçlar 30 saniyede iptal ediliyordu — sessiz bir hataydı.
      const sure=(/\/api\/v1\/(chat|chat-bolum|sentez|formul|kisisellestir|full|iliski|soru-cevap|sehir|manevi|rapor|rapor-bolum|rapor-pdf|onerilen-sorular|arz-izdusumu|kartografi-cizgi|rektifikasyon|solar-return-bagla)/.test(kaynak)
        || /\/api\/v2\/(bolum|belge|zaman)/.test(kaynak))
        ? ZIC_ZAMAN_ASIMI : 30000;
      const zamanlayici=setTimeout(()=>kt.abort(),sure);
      ayar.signal=kt.signal;
      return asil(kaynak,ayar).finally(()=>clearTimeout(zamanlayici));
    }
    return asil(kaynak,ayar);
  };
})();

/* ---- ROL ---- */
let ROL="yonetici", OTURUM=null, KILITLI_MODEL=null;
/* Misafir kategorileri sunucudan gelir (tek kaynak). Derinleştirme düğmesi
   mevcut bölüm analizi ucunu kullanır; eşleme burada. */
let MIS_KAT=[];
const MIS_BOLUM={dongu:"hukum",catal:"catal",egilim:"kutleler",
  direnc:"topoloji",gizli:"hudud",donem:"sira",nefes:"kabzbast",
  doku:"deneme",cag:"kadim",karar:"hd"};
(async function kategorileriYukle(){
  try{
    const r=await fetch("/api/v1/misafir-kategoriler");
    MIS_KAT=(await r.json()).kategoriler||[];
  }catch(e){ MIS_KAT=[]; }
})();

(async function girisKur(){
  let parolaGerekli=false;
  try{ const r=await fetch("/api/v1/rol-bilgi"); parolaGerekli=(await r.json()).parola_gerekli; }catch(e){}
  document.querySelectorAll(".rol-kart").forEach(b=>b.onclick=async()=>{
    const rol=b.dataset.rol;
    if(rol==="yonetici"){
      // Yönetici seçilince DAİMA parola sorulur. Sunucuda ADMIN_SIFRE
      // tanımlı değilse bu açıkça söylenir; sessizce içeri almak,
      // korumanın var sanılmasına yol açıyordu.
      $("girisParola").style.display="block";
      $("parolaHata").style.display=parolaGerekli?"none":"block";
      if(!parolaGerekli)$("parolaHata").textContent=
        "Sunucuda ADMIN_SIFRE tanımlı değil — giriş korumasız. "+
        "Render'da bu değişkeni ekleyip yeniden dağıtın.";
      $("parola").focus();
      return;
    }
    baslat(rol);
  });
  $("parolaGir").onclick=async()=>{
    try{
      const r=await fetch("/api/v1/rol-dogrula",{method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({parola:$("parola").value})});
      if(!r.ok)throw new Error((await r.json()).detail||"Parola hatalı");
      sessionStorage.setItem("zic_yon",$("parola").value);
      baslat("yonetici");
    }catch(e){ $("parolaHata").textContent=e.message; $("parolaHata").style.display="block"; }
  };
  $("parola").addEventListener("keydown",e=>{if(e.key==="Enter")$("parolaGir").click();});
})();

function baslat(rol){
  ROL=rol; try{misafirSadelestir();}catch(e){}
  $("giris").style.display="none";
  $("uygulama").style.display="block";
  document.body.classList.toggle("misafir-kip", rol==="misafir");
  document.body.classList.toggle("yonetici-kip", rol==="yonetici");
  const kh=document.querySelector(".kahraman h1");
  if(kh)kh.innerHTML=rol==="yonetici"
    ?'Analiz <em>konsolu</em>.<br>Önce omurga, sonra detay.'
    :'Doğum haritasını bir <em>alan</em> gibi okur.';
  const ka=$("kahramanAlt");
  if(ka)ka.textContent=rol==="yonetici"
    ?"Doğum verisini kur, kategori yoğunluğunu tara ve yalnız gerekli katmanlara in."
    :"Bilgilerinizi girin; teknik döküm yerine yorum ve danışman akışı gösterilir.";
  try{ yoneticiPanelKur(); }catch(e){}
  const ser=document.querySelector(".serit-meta");
  if(ser)ser.innerHTML=`<span>${rol==="misafir"?"Misafir":"Yönetici"}</span>`+
    `<span class="ayrac"></span><button type="button" class="rol-rozet" id="rolDegis">rol değiştir</button>`;
  const rd=$("rolDegis");
  if(rd)rd.onclick=()=>{ $("giris").style.display="flex"; $("uygulama").style.display="none";
    $("sonuc").style.display="none"; $("sonuc").innerHTML=""; SON_ANALIZ=null; OTURUM=null; KILITLI_MODEL=null; modelKilitle(false); };
}

const tzSel=$("tz"), tzSel2=$("tz2");
// Kullanıcı düzeltmeye başlayınca kırmızı işaret kalksın.
document.addEventListener("input",e=>{
  if(e.target.classList&&e.target.classList.contains("gecersiz"))
    e.target.classList.remove("gecersiz");
},true);
[tzSel,tzSel2].forEach(el=>TZLER.forEach(z=>el.add(new Option(z,z))));

/* ---- DOĞUM YERİ: ülke → bölge → şehir ----
   244 ülke, 34.000'den fazla şehir. Ülke dizini küçüktür (13 KB) ve açılışta
   yüklenir; şehir verisi ülke başına ayrı dosyadadır ve YALNIZ seçilen ülke
   indirilir. Türkiye için geonames'in 429 şehri yerine 81 il / 1037 ilçelik
   kendi veri setimiz kullanılır.
   Her şehir kaydı SAAT DİLİMİNİ de taşır; seçim yapılınca otomatik ayarlanır. */
let ULKELER=[], ULKE_ONBELLEK={};

async function ulkeYukle(kod){
  if(ULKE_ONBELLEK[kod])return ULKE_ONBELLEK[kod];
  const r=await fetch("/api/v1/ulke/"+kod);
  if(!r.ok)throw new Error("Ülke verisi alınamadı ("+r.status+")");
  const d=await r.json();
  ULKE_ONBELLEK[kod]=d;
  return d;
}

/* ---- TEMA ----
   Seçim cihazda saklanır; sayfa açılırken FLASH olmaması için en erken
   noktada uygulanır (aşağıdaki satır sayfa başında da çalışır). */
/* ---- OTURUM SÜREKLİLİĞİ ----
   Analiz, sohbet, sentez ve yazılmış rapor bölümleri sayfa yenilenince
   kayboluyordu. Bir saatlik seans tek bir yenilemeye kurban gidiyordu.
   Artık üretilen her şey cihazda saklanır; sayfa açıldığında devam
   teklif edilir. Sunucuya hiçbir şey gönderilmez. */
const OTURUM_ANAHTAR="zic_oturum_yedek";
let OTURUM_YAZ_ZAMANLAYICI=null;

function oturumYedekle(){
  clearTimeout(OTURUM_YAZ_ZAMANLAYICI);
  OTURUM_YAZ_ZAMANLAYICI=setTimeout(()=>{
    try{
      if(!SON_ANALIZ)return;
      const g=(SON_ANALIZ.girdi)||{};
      localStorage.setItem(OTURUM_ANAHTAR,JSON.stringify({
        an:Date.now(), ad:g.ad||"", dogum:g.an||"", mod:SON_MOD||"Kişisel",
        rol:ROL, analiz:SON_ANALIZ, oturum:OTURUM, model:KILITLI_MODEL,
        sohbet:(typeof SOHBET!=="undefined"?SOHBET:[]).slice(-24),
        sentez:(typeof SENTEZ_METNI!=="undefined"?SENTEZ_METNI:"")||"",
        rapor:RAPOR_BOLUMLERI||[], raporTur:RAPOR_TUR||""
      }));
    }catch(e){ /* kota dolabilir; sessiz geç */ }
  },600);
}

function oturumSil(){ try{ localStorage.removeItem(OTURUM_ANAHTAR); }catch(e){} }

function oturumTeklif(){
  let y=null;
  try{ y=JSON.parse(localStorage.getItem(OTURUM_ANAHTAR)||"null"); }catch(e){}
  if(!y||!y.analiz)return;
  const yas=Math.round((Date.now()-(y.an||0))/60000);
  if(yas>720){ oturumSil(); return; }           // 12 saatten eski atılır
  const kim=y.ad||y.dogum||"önceki oturum";
  const kutu=document.createElement("div");
  kutu.className="devam-serit";
  kutu.innerHTML=`<span><b>Yarım kalmış oturum:</b> ${esc(kim)}
    · ${yas<60?yas+" dk":Math.round(yas/60)+" sa"} önce
    ${(y.rapor||[]).length?`· ${y.rapor.length} rapor bölümü`:""}</span>
    <span><button type="button" id="devamEt">Devam et</button>
    <button type="button" id="devamSil">Sil</button></span>`;
  // Giriş perdesi açıksa onun İÇİNE konur; kapalıysa başlığın altına.
  const ic=document.querySelector(".giris-ic");
  const perde=$("giris");
  if(ic && perde && getComputedStyle(perde).display!=="none"){
    ic.appendChild(kutu);
  }else{
    const hedef=document.querySelector(".serlevha");
    if(hedef&&hedef.parentNode)hedef.parentNode.insertBefore(kutu,hedef.nextSibling);
  }
  $("devamSil").onclick=()=>{ oturumSil(); kutu.remove(); };
  $("devamEt").onclick=()=>{
    try{
      SON_ANALIZ=y.analiz; SON_MOD=y.mod; OTURUM=y.oturum||null;
      KILITLI_MODEL=y.model||((y.analiz.ai||{}).model)||null;
      if(typeof SOHBET!=="undefined")SOHBET=y.sohbet||[];
      if(typeof SENTEZ_METNI!=="undefined")SENTEZ_METNI=y.sentez||"";
      RAPOR_BOLUMLERI=y.rapor||[]; RAPOR_TUR=y.raporTur||"";
      if(y.rol&&y.rol!==ROL){ ROL=y.rol; }
      const gi=$("giris"); if(gi)gi.style.display="none";
      ciz(SON_ANALIZ);
      if(KILITLI_MODEL)modelKilitle(true,KILITLI_MODEL);
      kutu.remove();
      window.scrollTo({top:0,behavior:"smooth"});
    }catch(e){
      kutu.innerHTML='<span style="color:var(--kirmizi)">Oturum geri yüklenemedi.</span>';
    }
  };
}


const TEMA_ANAHTAR="zic_tema";
function temaUygula(t){
  document.documentElement.setAttribute("data-tema",t);
  document.querySelectorAll(".tema-sec button").forEach(b=>
    b.setAttribute("aria-pressed", b.dataset.t===t ? "true":"false"));
  try{ localStorage.setItem(TEMA_ANAHTAR,t); }catch(e){}
}
/* ---- MİSAFİR SADELEŞTİRME ----
   Misafir kendi bilgisini girip doğrudan okumasına ulaşmalı. Teknik alan,
   teknik uyarı ve iç terim görmemeli: "Berzah", "Kara Delik", "Placidus",
   "UTC", rektifikasyon paneli — hiçbiri onun işi değil.

   Yönetici bunların hepsini görmeye devam eder; yalnız görünürlük değişir,
   hesap değişmez. */
function misafirSadelestir(){
  const misafir = (typeof ROL !== "undefined") && ROL === "misafir";
  document.querySelectorAll('[data-teknik="1"]').forEach(e=>{
    e.hidden = misafir;
    e.style.display = misafir ? "none" : "";
  });
  document.querySelectorAll('[data-terim="1"]').forEach(e=>{
    e.hidden = misafir; e.style.display = misafir ? "none" : "";
  });
  document.querySelectorAll('[data-sade="1"]').forEach(e=>{
    e.hidden = !misafir; e.style.display = misafir ? "" : "none";
  });
  // Doğum anı önizlemesi: misafirde UTC ve saat dilimi kodu gösterilmez
  const o=$("onizleme");
  if(o) o.classList.toggle("sade", misafir);
  // Buton metni: misafirde daha davetkâr
  const b=$("btn");
  if(b && !b.dataset.aslen) b.dataset.aslen=b.textContent;
  if(b) b.textContent = misafir ? "Okumamı çıkar" : (b.dataset.aslen||b.textContent);
  const ma=$("modAciklama");
  if(ma && misafir) ma.textContent="Doğum bilgilerinizi girin, okumanız çıksın.";
}

/* ---- DOSYA İNDİRME ----
   Önceki kod bağlantıyı DOM'a EKLEMEDEN click() çağırıyordu. Masaüstü
   Chrome'da çalışır ama ANDROID CHROME BUNU SESSİZCE YOK SAYAR: hiçbir
   şey olmaz, hata da vermez. Kullanıcı "PDF kaydet dedim, ekrana hiçbir
   şey dönmedi" diyor — sebebi buydu.

   Artık: bağlantı belgeye eklenir, tıklanır, sonra kaldırılır. İndirme
   yine de olmazsa kullanıcıya DOKUNULABİLİR bir bağlantı gösterilir —
   sessiz başarısızlık yok. */
function dosyaIndir(blob, ad, kutu){
  let url;
  try{ url = URL.createObjectURL(blob); }
  catch(e){ if(kutu) kutu.innerHTML='<p class="ipucu" style="color:var(--kirmizi)">Dosya hazırlanamadı.</p>'; return false; }
  try{
    const a=document.createElement("a");
    a.href=url; a.download=ad; a.rel="noopener";
    a.style.display="none";
    document.body.appendChild(a);       // ← eksik olan buydu
    a.click();
    setTimeout(()=>{ try{ a.remove(); }catch(e){} }, 0);
  }catch(e){ /* aşağıdaki yedek bağlantı devreye girer */ }
  // Yedek: bazı tarayıcılarda program tıklaması engellenir. Elle
  // dokunulabilecek bir bağlantı bırakılır.
  if(kutu){
    kutu.innerHTML=`<p class="ipucu">Rapor hazır (${Math.round(blob.size/1024)} KB).
      İnmediyse buna dokunun:</p>
      <a class="indir" id="elleIndir" href="${url}" download="${esc(ad)}"
         style="display:inline-block;margin-top:8px">${esc(ad)}</a>`;
  }
  setTimeout(()=>{ try{ URL.revokeObjectURL(url); }catch(e){} }, 120000);
  return true;
}

/* ---- YAZI BOYUTU ----
   Temadan BAĞIMSIZ. En çok işe yarayan erişilebilirlik ayarı budur:
   kişi sevdiği temayı bırakmadan yazıyı büyütebilir. */
const BOY_ANAHTAR="zic_boy";
function boyUygula(b){
  const h=document.documentElement;
  if(b) h.setAttribute("data-boy",b); else h.removeAttribute("data-boy");
  document.querySelectorAll(".boy-sec button").forEach(x=>
    x.setAttribute("aria-pressed", (x.dataset.boy||"")===(b||"") ? "true":"false"));
  try{ localStorage.setItem(BOY_ANAHTAR,b||""); }catch(e){}
}

/* Temaların sırası — klavye kısayolu bu sırayla döner */
const TEMALAR=["bauhaus","brutalist","rasat","minyatur","okuma","gece","karsitlik"];

function temaKur(){
  let t="bauhaus";
  try{ t=localStorage.getItem(TEMA_ANAHTAR)||"bauhaus"; }catch(e){}
  if(!TEMALAR.includes(t)) t="bauhaus";
  temaUygula(t);
  document.querySelectorAll(".tema-sec button").forEach(b=>
    b.onclick=()=>temaUygula(b.dataset.t));

  let b="";
  try{ b=localStorage.getItem(BOY_ANAHTAR)||""; }catch(e){}
  boyUygula(b);
  document.querySelectorAll(".boy-sec button").forEach(x=>
    x.onclick=()=>boyUygula(x.dataset.boy||""));

  // Klavye: Alt+T tema değiştirir, Alt+A yazıyı büyütür.
  // Seans sırasında fareyle düğme aramak zaman kaybı.
  document.addEventListener("keydown",e=>{
    if(!e.altKey || e.ctrlKey || e.metaKey) return;
    const k=(e.key||"").toLowerCase();
    if(k==="t"){
      e.preventDefault();
      const s=document.documentElement.getAttribute("data-tema")||"bauhaus";
      temaUygula(TEMALAR[(TEMALAR.indexOf(s)+1)%TEMALAR.length]);
    }else if(k==="a"){
      e.preventDefault();
      const sira=["","buyuk","cok-buyuk"];
      const s=document.documentElement.getAttribute("data-boy")||"";
      boyUygula(sira[(sira.indexOf(s)+1)%sira.length]);
    }
  });
}

const SON_YER_ANAHTAR="zic_son_yer";
function sonYeriYaz(){
  try{
    localStorage.setItem(SON_YER_ANAHTAR, JSON.stringify({
      ulke:$("ulke").value, bolge:$("il").value,
      sehir:($("ilce").selectedOptions[0]||{}).text||"",
      tz:tzSel.value, ev:$("ev")?$("ev").value:null}));
  }catch(e){}
}
function sonYeriOku(){
  try{ return JSON.parse(localStorage.getItem(SON_YER_ANAHTAR)||"null"); }
  catch(e){ return null; }
}

function yerKur(ek){
  const sf=ek?"2":"";
  const uSel=$("ulke"+sf), bSel=$("il"+sf), sSel=$("ilce"+sf);
  if(!uSel)return;
  uSel.innerHTML="";
  ULKELER.forEach(u=>uSel.add(new Option(`${u.ad} (${u.sehir})`,u.kod)));
  uSel.value="TR";
  const bolgeDoldur=async(ilkBolge,ilkSehir)=>{
    bSel.innerHTML='<option>yükleniyor…</option>'; sSel.innerHTML="";
    let d;
    try{ d=await ulkeYukle(uSel.value); }
    catch(e){ bSel.innerHTML='<option>veri alınamadı</option>'; return; }
    const adlar=Object.keys(d.bolgeler).sort((a,b)=>a.localeCompare(b,"tr"));
    bSel.innerHTML="";
    adlar.forEach(a=>bSel.add(new Option(a==="—"?"(bölgesiz)":a,a)));
    if(ilkBolge&&adlar.includes(ilkBolge))bSel.value=ilkBolge;
    sehirDoldur(ilkSehir);
  };
  const sehirDoldur=(tercih)=>{
    const d=ULKE_ONBELLEK[uSel.value]; if(!d)return;
    const liste=d.bolgeler[bSel.value]||[];
    sSel.innerHTML="";
    liste.forEach((x,i)=>sSel.add(new Option(x.ad,i)));
    if(tercih){const j=liste.findIndex(x=>x.ad===tercih); if(j>=0)sSel.value=j;}
    uygula();
  };
  const uygula=()=>{
    const d=ULKE_ONBELLEK[uSel.value]; if(!d)return;
    const x=(d.bolgeler[bSel.value]||[])[+sSel.value]; if(!x)return;
    if(!ek)setTimeout(sonYeriYaz,0);
    $("enlem"+sf).value=(+x.lat).toFixed(4);
    $("boylam"+sf).value=(+x.lon).toFixed(4);
    // saat dilimi şehirden gelir; listede yoksa eklenir
    const tz=ek?tzSel2:tzSel;
    if(x.tz){
      if(![...tz.options].some(o=>o.value===x.tz))tz.add(new Option(x.tz,x.tz));
      tz.value=x.tz;
    }
    ek?onizle2():onizle();
  };
  uSel.onchange=()=>bolgeDoldur();
  bSel.onchange=()=>sehirDoldur();
  sSel.onchange=uygula;
  // Son kullanılan yer varsa oradan başla; yoksa varsayılan.
  const son=ek?null:sonYeriOku();
  if(son&&son.ulke){
    uSel.value=son.ulke;
    bolgeDoldur(son.bolge, son.sehir);
    if(son.tz){
      if(![...tzSel.options].some(o=>o.value===son.tz))tzSel.add(new Option(son.tz,son.tz));
      tzSel.value=son.tz;
    }
    if(son.ev&&$("ev"))$("ev").value=son.ev;
  }else{
    bolgeDoldur(ek?"İstanbul":"Kocaeli", ek?"İstanbul (merkez)":"Gebze");
  }
}

async function yerleriYukle(){
  try{
    const r=await fetch("/api/v1/ulkeler");
    ULKELER=(await r.json()).ulkeler||[];
  }catch(e){ ULKELER=[{kod:"TR",ad:"Türkiye",sehir:0}]; }
  yerKur(false); yerKur(true);
}
yerleriYukle();

/* ---- analiz modu ---- */
const MOD_ACIKLAMA={
  kisisel:"Tek doğum haritası: Kara Delik, Ak Delik ve Berzah kişinin kendi alanından çıkar.",
  sinastri:"İki harita üst üste konur: çapraz açılar, ev bindirmeleri ve her kişinin alanının ötekince ne kadar büküldüğü ölçülür.",
  kompozit:"İki haritanın orta noktalarından üçüncü bir harita kurulur — ilişkinin kendi Kara Deliği ve Berzahı."};
function modDegisti(){
  const m=$("mod").value;
  $("modAciklama").textContent=MOD_ACIKLAMA[m];
  const ikili=(m!=="kisisel");
  $("kisiB").style.display=ikili?"block":"none";
  $("kisiBasA").style.display=ikili?"flex":"none";
  $("btn").textContent=ikili?(m==="sinastri"?"Sinastriyi yorumla":"Kompoziti yorumla"):"Haritamı yorumla";
  $("ekOzetA").textContent=ikili?"Kişi A — ek katmanlar":"Ek katmanlar";
}
$("mod").addEventListener("change",modDegisti);
modDegisti();
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const say=v=>v==null?"—":v;

function girdiTopla(ek){
  const sf=ek?"2":"";
  const [Y,M,D]=$("tarih"+sf).value.split("-").map(Number);
  const [h,mi]=$("saat"+sf).value.split(":").map(Number);
  const g={name:$("ad"+sf).value||(ek?"B":"Danışan"),year:Y,month:M,day:D,hour:h,minute:mi,
    lat:parseFloat($("enlem"+sf).value),lng:parseFloat($("boylam"+sf).value),
    house_system:$("ev").value,months:18,days:365};
  const of=parseFloat($("ofset"+sf).value);
  if(!isNaN(of))g.tz_offset=of; else g.tz_name=(ek?tzSel2:tzSel).value;
  const isim=$("isim"+sf).value.trim(); if(isim)g.isim=isim;
  const anne=$("anne"+sf).value.trim(); if(anne)g.anne=anne;
  const srKut=$("srAktif"+sf);
  const sr=parseInt($("sryil"+sf).value);
  if((!srKut||srKut.checked)&&sr)g.sr_year=sr;
  return g;
}

function solarSecimKur(sf=""){
  const c=$("srAktif"+sf), y=$("sryil"+sf);
  if(!c||!y)return;
  const uygula=()=>{ y.disabled=!c.checked; c.closest("label")?.classList.toggle("aktif",c.checked); };
  c.addEventListener("change",uygula); uygula();
}
solarSecimKur(""); solarSecimKur("2");

/* ---- rektifikasyon olay satırları ---- */
function olaySatir(tarih,ad){
  const d=document.createElement("div"); d.className="olay-satir";
  d.innerHTML=`<label><span class="etiket">Tarih</span>
      <input type="date" class="olayTarih" value="${esc(tarih||"")}"></label>
    <label><span class="etiket">Ne oldu</span>
      <input class="olayAd" placeholder="taşınma, iş değişimi, kayıp…" value="${esc(ad||"")}"></label>
    <button type="button" title="Sil">×</button>`;
  d.querySelector("button").onclick=()=>d.remove();
  return d;
}
function olaylariTopla(){
  return [...document.querySelectorAll(".olay-satir")].map(r=>({
    tarih:r.querySelector(".olayTarih").value,
    ad:r.querySelector(".olayAd").value.trim()
  })).filter(o=>o.tarih);
}
if($("olayEkle")){
  $("olayEkle").onclick=()=>$("olayListe").appendChild(olaySatir());
  for(let i=0;i<3;i++)$("olayListe").appendChild(olaySatir());
}

/* Aşamalı ilerleme: sabit bir cümle yerine ne yapıldığını gösterir. */
let ASAMA_ZAMAN=null;
function asamaBaslat(el, asamalar){
  asamaDur(); let i=0;
  ASAMA_ZAMAN=setInterval(()=>{
    i++; if(i>=asamalar.length){asamaDur();return;}
    el.textContent=asamalar[i];
  }, 2200);
}
function asamaDur(){ if(ASAMA_ZAMAN){clearInterval(ASAMA_ZAMAN); ASAMA_ZAMAN=null;} }

/* FORM DOĞRULAMA — sessiz başarısızlığı bitirir.
   Zorunlu alan boşken tarayıcının kendi doğrulaması gönderimi engelliyor ama
   hiçbir şey göstermiyordu: kullanıcı tıklıyor, hiçbir şey olmuyordu. Üstelik
   girdiTopla() çöp üretiyordu (yıl 0, enlem null). Artık her alan açıkça
   sınanıyor, eksik olan işaretlenip odaklanılıyor. */
/* FastAPI doğrulama hatası bir DİZİ döndürür; doğrudan yazdırılınca
   "[object Object]" görünüyordu. Alan adı ve sebebi Türkçeye çevrilir. */
const ALAN_TR={year:"yıl",month:"ay",day:"gün",hour:"saat",minute:"dakika",
  lat:"enlem",lng:"boylam",tz_name:"saat dilimi",tz_offset:"saat farkı",
  house_system:"ev sistemi",name:"ad",isim:"isim",anne:"anne adı",
  sr_year:"solar return yılı",olaylar:"olaylar",soru:"soru",bolum:"bölüm"};
/* Kullanıcıya gösterilecek hata: iç bilgi sızdırmaz.
   "Failed to fetch", uç adresleri ve yığın izleri saldırgana bilgi verir;
   kullanıcıya da hiçbir şey kazandırmaz. Yapabileceği tek şey beklemek. */
function kullaniciyaHata(err){
  const m=String((err&&err.message)||err||"");
  if(/abort/i.test(m)||(err&&err.name==="AbortError"))
    return "Yanıt beklenenden uzun sürdü. Daha kısa bir soru sorun ya da "+
           "birazdan tekrar deneyin.";
  if(/429|çok fazla/i.test(m))
    return "Şu an çok fazla istek var. Birkaç dakika sonra tekrar deneyin.";
  if(/410|oturum/i.test(m))
    return "Oturumun süresi doldu. Analizi yeniden çalıştırın.";
  if(/401|anahtar|parola/i.test(m))
    return "Erişim izniniz doğrulanamadı. Sayfayı yenileyip tekrar girin.";
  return "Danışmana şu an ulaşılamıyor. Birazdan tekrar deneyin.";
}

function sunucuHatasi(d, kod){
  const g=d&&d.detail;
  if(typeof g==="string")return g;
  if(Array.isArray(g)){
    const p=g.slice(0,3).map(x=>{
      const yol=(x.loc||[]).filter(y=>typeof y==="string"&&y!=="body");
      const ad=ALAN_TR[yol[yol.length-1]]||yol.join(" › ")||"alan";
      const m=(x.msg||"").replace("Input should be","olmalı:")
                         .replace("Field required","zorunlu")
                         .replace("value is not a valid","geçersiz");
      return `${ad} — ${m}`;
    }).join(" · ");
    return p||"Girilen değerler geçersiz.";
  }
  if(kod===429)return "Çok fazla istek. Biraz bekleyip tekrar deneyin.";
  if(kod===401)return "Erişim anahtarı gerekli ya da hatalı.";
  if(kod===410)return "Oturum süresi doldu. Analizi yeniden çalıştırın.";
  if(kod===503)return "Danışman şu an yanıt vermiyor. Birazdan tekrar deneyin.";
  if(kod>=500)return "Bir şeyler ters gitti. Birazdan tekrar deneyin.";
  return "İşlem tamamlanamadı. Birazdan tekrar deneyin.";
}

function formDogrula(ek){
  const sf=ek?"2":"";
  const sorun=[];
  const alan=(id,ad,kosul)=>{
    const e=$(id+sf); if(!e)return;
    if(!e.value){
      e.classList.add("gecersiz");
      sorun.push({id:id+sf, ad, tur:"eksik"});
    }else if(kosul&&!kosul(e.value)){
      e.classList.add("gecersiz");
      sorun.push({id:id+sf, ad, tur:"gecersiz"});
    }else{
      e.classList.remove("gecersiz");
    }
  };
  alan("tarih","Doğum tarihi");
  alan("saat","Doğum saati");
  alan("enlem","Enlem",v=>{const n=parseFloat(v);return !isNaN(n)&&n>=-90&&n<=90;});
  alan("boylam","Boylam",v=>{const n=parseFloat(v);return !isNaN(n)&&n>=-180&&n<=180;});
  alan("tz","Saat dilimi");
  // tarih aralığı: efemeris 1800-2400 arası güvenilir
  const t=$("tarih"+sf);
  if(t&&t.value){
    const y=+t.value.split("-")[0];
    if(y<1800||y>2200){
      t.classList.add("gecersiz");
      sorun.push({id:"tarih"+sf, ad:"Doğum yılı 1800–2200 arasında olmalı",
                  tur:"ozel"});
    }
  }
  return sorun;
}

function sorunGoster(durum, sorunlar, ek){
  durum.style.display="block";
  durum.className="durum hata";
  const ozel=sorunlar.filter(x=>x.tur==="ozel").map(x=>x.ad);
  const eksik=sorunlar.filter(x=>x.tur==="eksik").map(x=>x.ad);
  const gecersiz=sorunlar.filter(x=>x.tur==="gecersiz").map(x=>x.ad);
  const parca=[];
  if(eksik.length)parca.push(eksik.join(", ")+(eksik.length>1?" alanları":" alanı")+" boş");
  if(gecersiz.length)parca.push(gecersiz.join(", ")+" geçersiz");
  ozel.forEach(o=>parca.push(o));
  durum.textContent=(ek?"İkinci kişi — ":"")+parca.join("; ")+".";
  const ilk=$(sorunlar[0].id);
  if(ilk){
    // kapalı bir panelin içindeyse önce onu aç
    const kap=ilk.closest("details");
    if(kap&&!kap.open)kap.open=true;
    ilk.scrollIntoView({block:"center",behavior:"smooth"});
    setTimeout(()=>ilk.focus(),300);
  }
}

let onizleZaman=null;
async function onizle(){
  const kutu=$("tzOnizleme");
  let g; try{g=girdiTopla();}catch(_){return;}
  if(!g.year||isNaN(g.lat)||isNaN(g.lng)){kutu.textContent="Tarih ve koordinat bekleniyor…";return;}
  try{
    const r=await fetch("/api/v1/tz-check",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const d=await r.json();
    if(!r.ok){kutu.className="onizleme uyari";kutu.textContent=sunucuHatasi(d,r.status);return;}
    kutu.className="onizleme"+(d.uyarilar.length?" uyari":"");
    kutu.innerHTML=`<b>${esc(d.yerel_saat)}</b> yerel → <b>${esc(d.utc_karsiligi)}</b><br>`+
      `${esc(d.kaynak)}<br>${d.enlem.toFixed(4)}°K &nbsp; ${d.boylam.toFixed(4)}°D`+
      d.uyarilar.map(u=>`<span class="u">${esc(u)}</span>`).join("");
  }catch(err){kutu.className="onizleme uyari";kutu.textContent="Doğrulama başarısız: "+err.message;}
}
let onizleZaman2=null;
async function onizle2(){
  const kutu=$("tzOnizleme2");
  let g; try{g=girdiTopla(true);}catch(_){return;}
  if(!g.year||isNaN(g.lat)||isNaN(g.lng)){kutu.textContent="Tarih ve koordinat bekleniyor…";return;}
  try{
    const r=await fetch("/api/v1/tz-check",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const d=await r.json();
    if(!r.ok){kutu.className="onizleme uyari";kutu.textContent=sunucuHatasi(d,r.status);return;}
    kutu.className="onizleme"+(d.uyarilar.length?" uyari":"");
    kutu.innerHTML=`<b>${esc(d.yerel_saat)}</b> yerel → <b>${esc(d.utc_karsiligi)}</b><br>`+
      `${esc(d.kaynak)}<br>${d.enlem.toFixed(4)}°K &nbsp; ${d.boylam.toFixed(4)}°D`+
      d.uyarilar.map(u=>`<span class="u">${esc(u)}</span>`).join("");
  }catch(err){kutu.className="onizleme uyari";kutu.textContent="Doğrulama başarısız: "+err.message;}
}
["tarih","saat","enlem","boylam","ofset"].forEach(id=>
  $(id).addEventListener("input",()=>{clearTimeout(onizleZaman);onizleZaman=setTimeout(onizle,350);}));
["tarih2","saat2","enlem2","boylam2","ofset2"].forEach(id=>
  $(id).addEventListener("input",()=>{clearTimeout(onizleZaman2);onizleZaman2=setTimeout(onizle2,350);}));
tzSel.addEventListener("change",onizle);
tzSel2.addEventListener("change",onizle2);
onizle();

document.getElementById("form").addEventListener("submit",async e=>{
  e.preventDefault();
  const btn=$("btn"), durum=$("durum"), mod=$("mod").value;
  const eskiEtiket=btn.textContent;

  // Gönderimden ÖNCE doğrula. Zorunlu alan boşken tarayıcının kendi
  // doğrulaması gönderimi engelliyor ama hiçbir şey göstermiyordu:
  // kullanıcı tıklıyor, hiçbir şey olmuyordu.
  const sorunA=formDogrula(false);
  if(sorunA.length){ sorunGoster(durum, sorunA, false); return; }
  if(mod!=="kisisel"){
    const sorunB=formDogrula(true);
    if(sorunB.length){ sorunGoster(durum, sorunB, true); return; }
  }

  const govde=girdiTopla();
  const modelSecimi=seciliModel();
  if(!modelSecimi){
    durum.style.display="block"; durum.className="durum hata";
    durum.textContent="Analize başlamadan önce bir AI modeli seçin.";
    const m=$("modelSec"); if(m)m.focus();
    return;
  }

  govde.yorumla=(ROL!=="misafir"); govde.model=modelSecimi;
  govde.rol=ROL;
  const olaylar=olaylariTopla();
  if($("rektPanel") && $("rektPanel").open && olaylar.length>=3){
    govde.rektifiye=true; govde.olaylar=olaylar;
  }
  let uc="/api/v1/full", yuk=govde;
  if(mod!=="kisisel"){ uc="/api/v1/iliski"; yuk={mod:mod,rol:ROL,a:govde,b:girdiTopla(true)}; }

  btn.disabled=true;btn.textContent="Yorumlanıyor…";
  durum.style.display="block";durum.className="durum";
  asamaBaslat(durum, govde.rektifiye
    ?["Aday saatler taranıyor…","Olaylarla eşleştiriliyor…","Harita kuruluyor…","Yorum yazılıyor…"]
    :mod==="kisisel"
    ?["Efemeris okunuyor…","Alan taranıyor…","Eşik hesaplanıyor…","Yorum yazılıyor…"]
    :["İki harita kuruluyor…","Alanlar bindiriliyor…","Yorum yazılıyor…"]);
  durum.textContent=govde.rektifiye
    ?"Aday saatler taranıyor…"
    :mod==="kisisel"
    ?"Efemeris okunuyor…"
    :"İki harita kuruluyor, alanlar üst üste bindiriliyor…";
  try{
    const r=await fetch(uc,{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(yuk)});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    asamaDur();
    durum.style.display="none";
    SON_ANALIZ=d; OTURUM=d.oturum||null;
    sahneAnalizSifirla();
    KILITLI_MODEL=((d.ai||{}).model)||modelSecimi;
    modelKilitle(true,KILITLI_MODEL);
    SON_MOD={kisisel:"Kişisel",sinastri:"Sinastri",kompozit:"Kompozit"}[mod];
    ciz(d);
    $("sonuc").style.display="block";
    $("sonuc").scrollIntoView({behavior:"smooth",block:"start"});
  }catch(err){
    asamaDur();
    // durum kutusu başarı yolunda gizleniyordu; çizim sonradan patlarsa hata
    // görünmez kalıyordu. Artık hata daima tekrar görünür kılınıyor.
    durum.style.display="block";
    durum.className="durum hata";
    durum.textContent=(/geçersiz|boş|olmalı/i.test(err.message)?err.message:kullaniciyaHata(err));
  }finally{btn.disabled=false;btn.textContent=eskiEtiket;}
});

/* ============ imza: Φ ALAN HALKASI ============ */
const BURC=["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"];
const BURC_GLIF=["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"];
/* Ev anlamları — çarkta fare imleciyle görünür. Numaraya bakıp
   "kaçıncı ev neydi" diye hatırlamaya gerek kalmasın. */
const EV_ANLAM=["kendilik, beden, ilk izlenim","sahip oldukların, kaynaklar",
 "yakın çevre, öğrenme, kardeşler","kök, ev, aile, geçmiş",
 "yaratma, çocuk, oyun, risk","gündelik iş, sağlık, düzen",
 "ortaklık, eş, karşıdaki","ortak kaynak, dönüşüm, kriz",
 "uzak, inanç, öğreti, yolculuk","kariyer, görünürlük, statü",
 "topluluk, dostlar, gelecek","geri çekilme, gizli olan, bırakma"];
// unsur tinti: ateş / toprak / hava / su — renk süs değil, bilgi
const UNSUR_TINT=["rgba(224,48,30,.14)","rgba(30,158,138,.14)","rgba(242,183,5,.20)","rgba(27,79,160,.12)"];
const GLIF={"Güneş":"☉","Ay":"☽","Merkür":"☿","Venüs":"♀","Mars":"♂","Jüpiter":"♃",
  "Satürn":"♄","Uranüs":"♅","Neptün":"♆","Plüton":"♇"};

/* Katmanlı, etkileşimli alan halkası.
   Katmanlar: ALAN (Φ) · AÇILAR (majör açı ağı) · EVLER (ev uçları ve numaraları)
              KAPILAR (64 heksagram) · MUNDAN (açısallık/Gauquelin ağırlığı)
   Gezegenin üzerine gelince ayrıntı paneli dolar. */
let HALKA_VERI=null, HALKA_KATMAN={alan:true,evler:true,noktalar:true,dereceler:false,acilar:false,deklinasyon:false,kapilar:false,mundan:false};
let HUDUD=null;   // deklinasyon katmanı verisi (halkada çizilir)
let HALKA_SETI=[], HALKA_SECIM=0, VURGU=null;
let CIFT="kapali";   // kapali | transit | sr — dış halka kaynağı
let TRANSIT=null, TAMEKRAN=false;

/* Analiz çıktısından çizilebilir haritaları toplar: natal, Solar Return,
   ilişki modunda A / B / Kompozit ve varsa onların SR haritaları. */
/* Misafir kipinde hesaplanmış noktaların teknik adları gizlenir. */
const NOKTA_SADE={"Kara Delik":"Asıl sebep","Ak Delik":"Dile gelen yan",
  "Berzah":"Karar eşiği","Kader Rezonansı":"Yön duygusu","Anti-KRN":"Karşı çekim",
  "Vahdet":"Toplanma noktası","Süveyda":"Sağlam merkez","İcâbet":"Açık kapı",
  "Noksan":"İnşa alanı","Ayna Ekseni":"Yansıma ekseni","Şi'râ":"Sabit yıldız"};
function noktaAdi(a){ return (ROL==="misafir" && NOKTA_SADE[a]) || a; }

function halkaSeti(d){
  const set=[];
  const ek=(ad,v2,not)=>{ if(v2&&v2.phi_alani) set.push({ad:ad,v2:v2,not:not||""}); };
  ek("Natal", d.berzah_v2);
  if(d.solar_v2&&d.solar_v2.berzah_v2) ek("Solar Return "+d.solar_v2.yil,d.solar_v2.berzah_v2,d.solar_v2.an);
  const adA=((d.girdi||{}).A||{}).ad||"Kişi A", adB=((d.girdi||{}).B||{}).ad||"Kişi B";
  ek(adA, d.A_berzah); ek(adB, d.B_berzah);
  if(d.A_solar_v2) ek(adA+" · SR "+d.A_solar_v2.yil, d.A_solar_v2.berzah_v2, d.A_solar_v2.an);
  if(d.B_solar_v2) ek(adB+" · SR "+d.B_solar_v2.yil, d.B_solar_v2.berzah_v2, d.B_solar_v2.an);
  if(d.kompozit) ek("Kompozit", d.kompozit.berzah_v2);
  return set;
}

const HALKA_ACILAR=[[0,"☌",8],[60,"⚹",5],[90,"□",7],[120,"△",7],[180,"☍",8]];

function halkaCiz(){
  const v2=HALKA_VERI; if(!v2)return "";
  // Kuşaklar çakışmayacak biçimde ayrıldı: burç 168-186, hesaplanan
  // noktalar 146-162, gezegenler 106-140, Φ alanı 44-100.
  const CX=200,CY=200,R_DIS=186,R_BURC=168,R_IC=140,R_ORTA=72,GENLIK=28;
  const P=v2.phi_alani.ornek;
  /* KLASİK HARİTA DÜZENİ: Yükselen SOLDA (saat 9 yönü), evler saat yönünün
     TERSİNE ilerler. Önceden çark 0° Koç tepede sabitti; bu astronomik bir
     çizim, astrolojik değil. Artık çark, ASC ekranın soluna gelecek biçimde
     döndürülür ve 1. ev doğrudan Yükselen'den başlar. */
  const ASC=(v2.asc!=null?v2.asc:(v2.ev_uclari&&v2.ev_uclari[0])||0);
  const xy=(lon,r)=>{
    // ekran açısı: (lon - ASC) kadar ilerle, sıfır noktası solda (180°)
    const a=(180-(lon-ASC))*Math.PI/180;
    return[CX+r*Math.cos(a),CY+r*Math.sin(a)];
  };
  const yay=(l1,l2,r1,r2)=>{
    const [x1,y1]=xy(l1,r2),[x2,y2]=xy(l2,r2),[x3,y3]=xy(l2,r1),[x4,y4]=xy(l1,r1);
    const buyuk=((l2-l1+360)%360)>180?1:0;
    // xy() artık ters yönde ilerliyor; süpürme bayrağı da tersine çevrildi
    return `M${x1},${y1} A${r2},${r2} 0 ${buyuk} 0 ${x2},${y2} L${x3},${y3} A${r1},${r1} 0 ${buyuk} 1 ${x4},${y4} Z`;
  };
  const yaricap=p=>R_ORTA+GENLIK*(0.5-p)*2;
  let g="";

  // burç kadranı — glif + derece taksimatı (profesyonel çark standardı)
  for(let i=0;i<12;i++){
    g+=`<path d="${yay(i*30,(i+1)*30,R_BURC,R_DIS)}" fill="${UNSUR_TINT[i%4]}" stroke="rgba(20,17,15,.28)" stroke-width="1"><title>${BURC[i]}</title></path>`;
    const [tx,ty]=xy(i*30+15,(R_BURC+R_DIS)/2);
    g+=`<text x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" font-size="13" fill="#14110F" text-anchor="middle" dominant-baseline="central">${BURC_GLIF[i]}</text>`;
  }
  // derece taksimatı: 1° küçük, 5° orta, 10° uzun
  for(let d=0;d<360;d++){
    const uz=(d%10===0)?6:(d%5===0)?4:2;
    const [x1,y1]=xy(d,R_BURC),[x2,y2]=xy(d,R_BURC-uz);
    g+=`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="rgba(20,17,15,${d%10===0?.42:d%5===0?.3:.16})" stroke-width="${d%10===0?0.9:0.6}"/>`;
  }

  // KATMAN: kapılar (64 heksagram dilimi)
  if(HALKA_KATMAN.kapilar){
    for(let k=0;k<64;k++){
      const a1=(302+k*5.625)%360;
      const [x1,y1]=xy(a1,R_BURC),[x2,y2]=xy(a1,R_BURC-9);
      g+=`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="rgba(27,79,160,.5)" stroke-width="1"/>`;
    }
    (v2.yapisal_ikizler||[]).forEach(t=>{
      const a=(v2.kutleler.find(m=>m.gezegen===t.a)||{}).lon;
      const b=(v2.kutleler.find(m=>m.gezegen===t.b)||{}).lon;
      if(a==null||b==null)return;
      const [x1,y1]=xy(a,R_IC-18),[x2,y2]=xy(b,R_IC-18);
      g+=`<path d="M${x1},${y1} Q200,200 ${x2},${y2}" fill="none" stroke="#1B4FA0" stroke-width="1.6" stroke-dasharray="4 4" opacity=".75"/>`;
    });
  }

  // KATMAN: evler
  if(HALKA_KATMAN.evler && v2.ev_uclari){
    v2.ev_uclari.forEach((c,i)=>{
      const [x1,y1]=xy(c,R_ORTA+GENLIK+6),[x2,y2]=xy(c,R_BURC);
      const kose=(i%3===0);
      g+=`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="#14110F" stroke-width="${kose?2:0.9}" opacity="${kose?.85:.4}"/>`;
      const orta=v2.ev_uclari[(i+1)%12];
      const yay_orta=(c+((orta-c+360)%360)/2)%360;
      const [tx,ty]=xy(yay_orta,R_IC-44);
      const evAd=EV_ANLAM[i]||"";
      g+=`<text x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" font-size="8.5" fill="rgba(20,17,15,.55)" text-anchor="middle" dominant-baseline="central" font-family="JetBrains Mono,monospace">${i+1}<title>${i+1}. ev — ${evAd}</title></text>`;
    });
  }

  // KATMAN: açılar (bir gezegen seçiliyse otomatik açılır)
  if(HALKA_KATMAN.acilar || VURGU){
    const K=v2.kutleler;
    for(let i=0;i<K.length;i++)for(let j=i+1;j<K.length;j++){
      let d=Math.abs(K[i].lon-K[j].lon)%360; if(d>180)d=360-d;
      for(const [ang,gl,orb] of HALKA_ACILAR){
        const o=Math.abs(d-ang);
        if(o<=orb){
          const renk=(ang===90||ang===180)?"#E0301E":(ang===0?"#14110F":"#1E9E8A");
          const [x1,y1]=xy(K[i].lon,R_ORTA+GENLIK),[x2,y2]=xy(K[j].lon,R_ORTA+GENLIK);
          const vur=!VURGU||K[i].gezegen===VURGU||K[j].gezegen===VURGU;
          g+=`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${renk}" stroke-width="${((vur?2.6:1.2)*(1-o/orb)+0.4).toFixed(2)}" opacity="${vur?0.95:0.16}"/>`;
          break;
        }
      }
    }
  }

  // KATMAN: deklinasyon — paralel bağlar ve hudûd dışı cisimler
  // Bunlar boylamda görünmez; çarkta gösterilmezse hiç fark edilmezler.
  if(HALKA_KATMAN.deklinasyon && HUDUD && HUDUD.paralel){
    const konum={}; (v2.kutleler||[]).forEach(m=>konum[m.gezegen]=m.lon);
    (HUDUD.paralel.temaslar||[]).forEach(t=>{
      const l1=konum[t.a], l2=konum[t.b];
      if(l1==null||l2==null)return;
      const [x1,y1]=xy(l1,R_ORTA+GENLIK+10),[x2,y2]=xy(l2,R_ORTA+GENLIK+10);
      const renk=(t.tur==="paralel")?"#1B4FA0":"#8B5CF6";
      g+=`<path d="M${x1.toFixed(1)},${y1.toFixed(1)} Q200,200 ${x2.toFixed(1)},${y2.toFixed(1)}" fill="none" stroke="${renk}" stroke-width="${t.gizli?2:1}" stroke-dasharray="${t.gizli?"":"3 3"}" opacity="${t.gizli?.85:.4}"/>`;
    });
    const oob=new Set(((HUDUD.hudud_disi||{}).hudud_disi||[]).map(x=>x.cisim));
    (v2.kutleler||[]).forEach(m=>{
      if(!oob.has(m.gezegen))return;
      const [ox,oy]=xy(m.lon,R_DIS+1);
      g+=`<circle cx="${ox.toFixed(1)}" cy="${oy.toFixed(1)}" r="4.5" fill="none" stroke="#8B5CF6" stroke-width="2"/>`;
    });
  }

  // KATMAN: Φ alanı
  if(HALKA_KATMAN.alan){
    let yol="";
    for(let i=0;i<=360;i++){const [x,y]=xy(i,yaricap(P[i%360]));yol+=(i?"L":"M")+x.toFixed(1)+","+y.toFixed(1);}
    g+=`<circle cx="200" cy="200" r="${R_ORTA}" fill="none" stroke="rgba(20,17,15,.16)" stroke-width="1" stroke-dasharray="2 6"/>`;
    g+=`<path d="${yol}Z" fill="rgba(20,17,15,.045)" stroke="#14110F" stroke-width="2"/>`;
  }

  // gezegenler
  const sirali=[...v2.kutleler].sort((a,b)=>a.lon-b.lon);
  const KADEME=[R_IC-2,R_IC-16,R_IC-30];
  let sonLon=-99,kat=0;
  sirali.forEach(m=>{
    kat=(m.lon-sonLon<14)?(kat+1)%3:0; sonLon=m.lon;
    const r=KADEME[kat],[x,y]=xy(m.lon,r);
    const yc=7.5+Math.min(3.5,Math.abs(m.m)*0.5);
    const [lx,ly]=xy(m.lon,R_IC+6);
    // mundan katmanı: açısallık ağırlığını halka kalınlığıyla göster
    const ang=(m.bilesenler&&m.bilesenler["açısal"])||1;
    const vurgu=HALKA_KATMAN.mundan?Math.max(0,(ang-1))*4.5:0;
    if(vurgu>0.3)g+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(yc+vurgu).toFixed(1)}" fill="none" stroke="#F2B705" stroke-width="2.4" opacity=".85"/>`;
    g+=`<line x1="${lx.toFixed(1)}" y1="${ly.toFixed(1)}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="rgba(20,17,15,.28)" stroke-width="1"/>`;
    g+=`<g class="gez" data-ad="${esc(m.gezegen)}" style="cursor:pointer">
      <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(yc+7).toFixed(1)}" fill="transparent"/>
      <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${yc.toFixed(1)}" fill="#FFFFFF" stroke="${m.retro?'#E0301E':'#14110F'}" stroke-width="1.4"/>
      <text x="${x.toFixed(1)}" y="${y.toFixed(1)}" font-size="10" fill="${m.retro?'#E0301E':'#14110F'}" text-anchor="middle" dominant-baseline="central">${GLIF[m.gezegen]||"·"}</text>${
        m.retro?`<text x="${(x+yc+0.5).toFixed(1)}" y="${(y-yc+1.5).toFixed(1)}" font-size="7.5" fill="#E0301E" text-anchor="middle" dominant-baseline="central">℞</text>`:""}</g>`;
    // Derece etiketi ayrı katman: çark zaten kalabalık, varsayılan kapalı.
    // Açıkken her gezegenin kendi kademesinde, dairenin hemen içinde yazılır.
    if(HALKA_KATMAN.dereceler){
      const [dx,dy]=xy(m.lon,r-yc-6.5);
      const der=Math.floor(m.lon%30), dak=Math.round((m.lon%1)*60)%60;
      g+=`<text x="${dx.toFixed(1)}" y="${dy.toFixed(1)}" font-size="6" fill="rgba(20,17,15,.72)" text-anchor="middle" dominant-baseline="central" font-family="JetBrains Mono,monospace">${der}°${String(dak).padStart(2,"0")}</text>`;
    }
  });

  // KATMAN: hesaplanan noktalar (KRN, Vahdet, Süveyda, İcâbet, Noksan, Şi'râ…)
  // Bunlar cisim değil, türetilmiş yerlerdir; çark üzerinde gezegen gibi
  // konumlanır ve gezegenlerle açı yaparlar.
  if(HALKA_KATMAN.noktalar && v2.noktalar){
    // nokta–gezegen açıları
    (v2.nokta_acilari||[]).forEach(a=>{
      const [x1,y1]=xy(a.n_lon,R_ORTA+GENLIK+4),[x2,y2]=xy(a.h_lon,R_ORTA+GENLIK+4);
      const renk=(a.aci==="Kare"||a.aci==="Karşıt")?"#E0301E":
                 (a.aci==="Kavuşum"?"#14110F":"#1E9E8A");
      const vur=!VURGU||a.kod===VURGU||a.hedef_kod===VURGU||a.hedef===VURGU;
      g+=`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${renk}" stroke-width="${vur?2.2:0.8}" stroke-dasharray="3 3" opacity="${vur?0.9:0.14}"/>`;
    });
    const nsir=[...v2.noktalar].sort((a,b)=>a.lon-b.lon);
    let nson=-99,nkat=0;
    const NK=[R_BURC-8,R_BURC-22];
    nsir.forEach(nk=>{
      nkat=(nk.lon-nson<12)?(nkat+1)%2:0; nson=nk.lon;
      const r=NK[nkat],[x,y]=xy(nk.lon,r);
      const [lx,ly]=xy(nk.lon,R_BURC-1);
      g+=`<line x1="${lx.toFixed(1)}" y1="${ly.toFixed(1)}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="rgba(242,183,5,.7)" stroke-width="1"/>`;
      g+=`<g class="nkt" data-kod="${esc(nk.kod)}" style="cursor:pointer">
        <title>${esc(noktaAdi(nk.ad))} · ${esc(nk.konum||"")}${nk.ev?" · "+nk.ev+". ev":""}</title>`;
      g+=`
        <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="10" fill="transparent"/>
        <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="7" fill="#F2B705" stroke="#14110F" stroke-width="1.2"/>
        <text x="${x.toFixed(1)}" y="${y.toFixed(1)}" font-size="8" fill="#14110F" text-anchor="middle" dominant-baseline="central">${nk.glif}</text></g>`;
    });
  }

  // ÇİFT ÇARK — dış halka. Profesyonel yazılımların bi-wheel'i: içeride
  // natal, dışarıda transit ya da Solar Return. Zodyak bandının dışına
  // çizilir; böylece iç çarkın geometrisi hiç bozulmaz.
  if(CIFT!=="kapali"){
    let dis=null, disAcilar=[];
    if(CIFT==="transit" && TRANSIT && TRANSIT.cisimler){
      dis=TRANSIT.cisimler; disAcilar=TRANSIT.acilar||[];
    }else if(CIFT==="sr"){
      const sr=HALKA_SETI.find(h=>/Solar/.test(h.ad));
      if(sr&&sr.v2&&sr.v2.kutleler)
        dis=sr.v2.kutleler.map(m=>({gezegen:m.gezegen,lon:m.lon,konum:m.konum,retro:m.retro}));
    }
    if(dis&&dis.length){
      const R_DIS2=R_DIS+30, R_DIS1=R_DIS+8;
      g+=`<circle cx="200" cy="200" r="${R_DIS2}" fill="none" stroke="rgba(20,17,15,.3)" stroke-width="1"/>`;
      g+=`<circle cx="200" cy="200" r="${R_DIS1}" fill="none" stroke="rgba(20,17,15,.18)" stroke-width="1"/>`;
      // dış–iç açı çizgileri (yalnız transit kipinde hesaplanmış olanlar)
      disAcilar.forEach(a=>{
        const [x1,y1]=xy(a.d_lon,R_ORTA+GENLIK+2),[x2,y2]=xy(a.n_lon,R_ORTA+GENLIK+2);
        const renk=(a.aci==="Kare"||a.aci==="Karşıt")?"#E0301E":
                   (a.aci==="Kavuşum"?"#14110F":"#1E9E8A");
        g+=`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${renk}" stroke-width="0.9" stroke-dasharray="2 4" opacity=".5"/>`;
      });
      const ds=[...dis].sort((a,b)=>a.lon-b.lon);
      let dson=-99,dkat=0; const DK=[(R_DIS1+R_DIS2)/2, R_DIS2-6];
      ds.forEach(m=>{
        dkat=(m.lon-dson<11)?(dkat+1)%2:0; dson=m.lon;
        const [x,y]=xy(m.lon,DK[dkat]);
        const [tx,ty]=xy(m.lon,R_DIS+1);
        g+=`<line x1="${tx.toFixed(1)}" y1="${ty.toFixed(1)}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="rgba(20,17,15,.25)" stroke-width="0.8"/>`;
        g+=`<g class="dis" data-ad="${esc(m.gezegen)}" data-lon="${m.lon}" style="cursor:pointer">
          <title>${esc(m.gezegen)} (dış çark) · ${esc(m.konum||"")}${m.retro?" · geri":""}</title>`;
        g+=`
          <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="9" fill="transparent"/>
          <text x="${x.toFixed(1)}" y="${y.toFixed(1)}" font-size="10" fill="${m.retro?'#E0301E':'#1B4FA0'}" text-anchor="middle" dominant-baseline="central">${GLIF[m.gezegen]||"·"}</text></g>`;
      });
    }
  }

  // Köşeler: ASC solda, MC yukarıda — okuyanın yönünü bulması için etiketli
  if(v2.ev_uclari && v2.ev_uclari.length===12){
    const kose=[[v2.ev_uclari[0],"ASC"],[v2.ev_uclari[3],"IC"],
                [v2.ev_uclari[6],"DSC"],[v2.ev_uclari[9],"MC"]];
    kose.forEach(([lon,ad])=>{
      const [x1,y1]=xy(lon,R_ORTA+GENLIK+6),[x2,y2]=xy(lon,R_DIS);
      g+=`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="#14110F" stroke-width="1.8" opacity=".8"/>`;
      const [tx,ty]=xy(lon,R_DIS+9);
      const koseAd={ASC:"Yükselen — dışa dönük yüzün",MC:"Tepe noktası — görünürlüğün",
                    DSC:"Batan — karşındaki",IC:"Dip — kökün"}[ad]||ad;
      g+=`<text x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" font-size="8.5" fill="#14110F" text-anchor="middle" dominant-baseline="central" font-family="JetBrains Mono,monospace" font-weight="bold">${ad}<title>${koseAd}</title></text>`;
    });
  }

  // KD / AD / Berzah
  const kd=v2.KD.lon, ad=v2.AD.lon, b=v2.berzah;
  const rk=HALKA_KATMAN.alan?yaricap(P[Math.round(kd)%360]):R_ORTA;
  const ra=HALKA_KATMAN.alan?yaricap(P[Math.round(ad)%360]):R_ORTA;
  const [kx,ky]=xy(kd,rk),[ax,ay]=xy(ad,ra);
  g+=`<line x1="${kx.toFixed(1)}" y1="${ky.toFixed(1)}" x2="${ax.toFixed(1)}" y2="${ay.toFixed(1)}" stroke="rgba(20,17,15,.45)" stroke-width="1" stroke-dasharray="6 5"/>`;
  g+=`<circle cx="${kx.toFixed(1)}" cy="${ky.toFixed(1)}" r="9" fill="#14110F"/>`;
  g+=`<circle cx="${ax.toFixed(1)}" cy="${ay.toFixed(1)}" r="9" fill="#FFFFFF" stroke="#14110F" stroke-width="1.6"/>`;
  g+=`<circle cx="${ax.toFixed(1)}" cy="${ay.toFixed(1)}" r="3.4" fill="none" stroke="#14110F" stroke-width="1.6"/>`;
  if(b){
    const rb=HALKA_KATMAN.alan?yaricap(P[Math.round(b.lon)%360]):R_ORTA;
    const [bx,by]=xy(b.lon,rb);
    g+=`<rect x="${(bx-6.5).toFixed(1)}" y="${(by-6.5).toFixed(1)}" width="13" height="13" fill="#F2B705" stroke="#14110F" stroke-width="1.4" transform="rotate(45 ${bx.toFixed(1)} ${by.toFixed(1)})"/>`;
  }
  const pay=(CIFT!=="kapali")?46:14;
  return `<svg class="halka" viewBox="${-pay} ${-pay} ${400+2*pay} ${400+2*pay}" role="img" aria-label="Φ alan halkası — Yükselen solda">${g}</svg>`;
}

/* Açı ızgarası — profesyonel astroloji yazılımlarının üçgen matrisi.
   Satır/sütun kesişiminde iki cismin açısı ve orbu görünür. */
/* Unsur / nitelik / yarımküre dengesi — her profesyonel haritada bulunur.
   Klasik yöntem cisimleri sayar; burada KÜTLE ile ağırlıklandırılıyor, çünkü
   bu modelde her cismin ağırlığı farklı. Ham sayım da parantezde verilir. */
function dagilim(v2){
  const K=(v2.kutleler||[]); if(!K.length)return "";
  const UNSUR=["Ateş","Toprak","Hava","Su"], NITELIK=["Öncü","Sabit","Değişken"];
  const UR=["#E0301E","#1E9E8A","#F2B705","#1B4FA0"];
  const u=[0,0,0,0], us=[0,0,0,0], n=[0,0,0], ns=[0,0,0];
  let dogu=0, bati=0, kuzey=0, guney=0;
  const asc=(v2.asc!=null?v2.asc:0);
  K.forEach(m=>{
    const b=Math.floor(((m.lon%360)+360)%360/30);
    const w=Math.abs(m.m);
    u[b%4]+=w; us[b%4]++; n[b%3]+=w; ns[b%3]++;
    const ev=(function(){ if(!v2.ev_uclari)return null;
      for(let i=0;i<12;i++){const a=v2.ev_uclari[i],c=v2.ev_uclari[(i+1)%12];
        if(((m.lon-a)%360+360)%360 < ((c-a)%360+360)%360) return i+1;} return null;})();
    if(ev){ (ev>=1&&ev<=6?kuzey:guney); if(ev>=1&&ev<=6)kuzey+=w; else guney+=w;
            if(ev>=10||ev<=3)dogu+=w; else bati+=w; }
  });
  const cubuk=(etiketler,degerler,sayilar,renkler)=>{
    const top=degerler.reduce((a,b)=>a+b,0)||1;
    return `<div class="dag-grup">${etiketler.map((e,i)=>`
      <div class="dag-satir">
        <span class="dag-ad">${e}</span>
        <span class="dag-yol"><span class="dag-dolu" style="width:${(degerler[i]/top*100).toFixed(0)}%;background:${renkler?renkler[i]:"var(--murekkep)"}"></span></span>
        <span class="dag-say">%${(degerler[i]/top*100).toFixed(0)}${sayilar?` (${sayilar[i]})`:""}</span>
      </div>`).join("")}</div>`;
  };
  const yk=kuzey+guney||1, db=dogu+bati||1;
  return `<div class="dagilim">
    <div><h4>Unsur</h4>${cubuk(UNSUR,u,us,UR)}</div>
    <div><h4>Nitelik</h4>${cubuk(NITELIK,n,ns)}</div>
    <div><h4>Yarımküre</h4>${cubuk(["İç (1-6. ev)","Dış (7-12. ev)"],[kuzey,guney])}
      ${cubuk(["Doğu (kendi)","Batı (öteki)"],[dogu,bati])}</div>
  </div>
  <p class="usul">Kütleyle ağırlıklandırılmış; parantezdeki sayı ham cisim
  sayısıdır. İç yarımküre kişisel alan, dış yarımküre başkalarıyla kurulan
  hayattır; doğu kendi başlattığı, batı karşılık verdiği yandır.</p>`;
}

function aciIzgarasi(v2){
  const K=(v2.kutleler||[]);
  if(!K.length)return "<p>Veri yok.</p>";
  let h='<table class="cizelge izgara-aci"><thead><tr><th></th>';
  K.forEach(m=>h+=`<th title="${esc(m.gezegen)}">${GLIF[m.gezegen]||"·"}</th>`);
  h+="</tr></thead><tbody>";
  K.forEach((a,i)=>{
    h+=`<tr><th title="${esc(a.gezegen)}">${GLIF[a.gezegen]||"·"} ${esc(a.gezegen)}</th>`;
    K.forEach((b,j)=>{
      if(j>=i){h+='<td class="bos"></td>';return;}
      let d=Math.abs(a.lon-b.lon)%360; if(d>180)d=360-d;
      let hu="";
      for(const [ang,gl,orb] of HALKA_ACILAR){
        const o=Math.abs(d-ang);
        if(o<=orb){
          const sert=(ang===90||ang===180);
          hu=`<span class="ac ${sert?"sert":ang===0?"kav":"akis"}" title="${gl} ${o.toFixed(2)}°">${gl}<i>${o.toFixed(1)}</i></span>`;
          break;
        }
      }
      h+=`<td class="sayi">${hu}</td>`;
    });
    h+="</tr>";
  });
  return h+"</tbody></table>";
}

function halkaYenile(){
  const kap=document.getElementById("halkaCizim");
  if(!kap)return;
  kap.innerHTML=halkaCiz();
  const ti=document.getElementById("tamIc");
  if(ti)ti.innerHTML=halkaCiz();      // tam ekran açıksa o da tazelenir
  kap.querySelectorAll(".nkt").forEach(el=>{
    const gos=(tikla)=>{
      const n=(HALKA_VERI.noktalar||[]).find(x=>x.kod===el.dataset.kod);
      if(!n)return;
      const ac=(HALKA_VERI.nokta_acilari||[]).filter(a=>a.kod===n.kod).slice(0,3);
      document.getElementById("halkaBilgi").innerHTML=
        `<b>${n.glif} ${esc(noktaAdi(n.ad))}</b> ${esc(n.konum)}${n.ev?" · "+n.ev+". ev":""}<br>`+
        `<span class="ince">${ac.length?ac.map(a=>a.glif+" "+esc(a.hedef)+" ("+a.orb+"°)").join(" · ")
          :"gezegenlerle yakın bağ yok"}</span>`;
      // Tıklamada noktanın açıları çarkta da vurgulanır — gezegenlerde
      // olan davranışın aynısı; önceden yalnız metin görünüyordu.
      if(tikla===true){
        VURGU=(VURGU===n.kod)?null:n.kod;
        halkaYenile();
      }
    };
    el.addEventListener("mouseenter",()=>{ if(!VURGU) gos(false); });
    el.addEventListener("click",()=>gos(true));
  });
  kap.querySelectorAll(".gez").forEach(el=>{
    const bilgi=()=>{
      const m=HALKA_VERI.kutleler.find(x=>x.gezegen===el.dataset.ad);
      if(!m)return;
      const bl=m.bilesenler||{};
      // bu gezegenin gezegenlerle açıları — çarkta ayrıca vurgulanır
      const ac=[];
      (HALKA_VERI.kutleler||[]).forEach(o=>{
        if(o.gezegen===m.gezegen)return;
        let dd=Math.abs(m.lon-o.lon)%360; if(dd>180)dd=360-dd;
        for(const [ang,gl,orb] of HALKA_ACILAR){
          const oo=Math.abs(dd-ang);
          if(oo<=orb){ac.push(`${gl} ${o.gezegen} (${oo.toFixed(1)}°)`);break;}
        }
      });
      (HALKA_VERI.nokta_acilari||[]).filter(a=>a.hedef===m.gezegen)
        .forEach(a=>ac.push(`${a.glif} ${a.nokta} (${a.orb}°)`));
      document.getElementById("halkaBilgi").innerHTML=
        `<b>${esc(m.gezegen)}</b> ${esc(m.konum)} · kütle ${m.m>0?"+":""}${m.m}`+
        `${m.retro?' <span style="color:var(--kirmizi)">℞ geri hareket</span>':""}<br>`+
        `<span class="ince">asalet ${bl["asalet"]} · hız ${bl["hız"]} · açısal ${bl["açısal"]} · görünür ${bl["görünür"]} · dekl ${bl["dekl"]}</span>`+
        (ac.length?`<br><span class="ince">açılar: ${esc(ac.join("  ·  "))}</span>`:"");
      // seçili gezegenin açı çizgilerini öne çıkar
      VURGU=(VURGU===m.gezegen)?null:m.gezegen;
      halkaYenile();
      const y=document.querySelector(`.gez[data-ad="${CSS.escape(m.gezegen)}"]`);
      if(y)y.classList.add("secili");
    };
    el.addEventListener("mouseenter",()=>{ if(!VURGU) bilgi(); });
    el.addEventListener("click",bilgi);
  });
}

function halka(v2){
  HALKA_VERI=v2;
  const anahtarlar=[["evler","Evler"],["noktalar","Hesaplanan noktalar"],
                    ["dereceler","Dereceler"],["deklinasyon","Deklinasyon"],
                    ["alan","Φ alanı"],["acilar","Açılar"],
                    ["kapilar","64 kapı"],["mundan","Açısallık"]];
  const haritaSecici = HALKA_SETI.length>1
    ? `<div class="halka-harita">
         <span class="et">Harita</span>
         ${HALKA_SETI.map((h,i)=>`<button type="button" class="harita ${i===HALKA_SECIM?"acik":""}" data-h="${i}">${esc(h.ad)}</button>`).join("")}
       </div>` : "";
  return `${haritaSecici}
    <div class="halka-harita">
      <span class="et">Çift çark</span>
      <button type="button" class="ccark ${CIFT==="kapali"?"acik":""}" data-c="kapali">Kapalı</button>
      <button type="button" class="ccark ${CIFT==="transit"?"acik":""}" data-c="transit">Bugünkü gökyüzü</button>
      <button type="button" class="ccark ${CIFT==="sr"?"acik":""}" data-c="sr">Solar Return</button>
      <button type="button" class="ccark" id="tamEkran" title="Büyüt">⤢ Büyüt</button>
    </div>
    <div class="halka-arac">${anahtarlar.map(([k,ad])=>
      `<button type="button" class="katman ${HALKA_KATMAN[k]?"acik":""}" data-k="${k}">${ad}</button>`).join("")}
    </div>
    <div id="halkaCizim"></div>
    <details class="ek" style="margin-top:16px;border-top:none;padding-top:0">
      <summary>Denge dağılımı</summary>
      ${dagilim(v2)}
    </details>
    <details class="ek" style="margin-top:0;border-top:none;padding-top:0">
      <summary>Açı ızgarası</summary>
      <div class="sarma" style="margin-top:14px">${aciIzgarasi(v2)}</div>
    </details>
    <details class="ek" style="margin-top:0;border-top:none;padding-top:0">
      <summary>Konum tablosu</summary>
      <div class="sarma" style="margin-top:14px">
        <table class="cizelge"><thead><tr><th>Cisim</th><th>Konum</th><th>Ev</th><th>Kütle</th></tr></thead>
        <tbody>${(v2.kutleler||[]).map(m=>`<tr><td>${GLIF[m.gezegen]||""} ${esc(m.gezegen)}${m.retro?" ℞":""}</td><td class="sayi">${esc(m.konum)}</td><td class="sayi">${v2.ev_uclari?(function(){let e=null;for(let i=0;i<12;i++){const a=v2.ev_uclari[i],b=v2.ev_uclari[(i+1)%12];if(((m.lon-a)%360+360)%360 < ((b-a)%360+360)%360){e=i+1;break;}}return e||"—";})():"—"}</td><td class="sayi">${m.m>0?"+":""}${m.m}</td></tr>`).join("")}
        ${(v2.noktalar||[]).map(n=>`<tr><td>${n.glif} ${esc(n.ad)}</td><td class="sayi">${esc(n.konum||"")}</td><td class="sayi">${n.ev||"—"}</td><td class="sayi">—</td></tr>`).join("")}
        </tbody></table>
      </div>
    </details>
    <button type="button" class="indir" id="svgIndir" style="margin-top:14px">Çarkı SVG indir</button>
    <div class="halka-bilgi" id="halkaBilgi">Bir gezegene ya da sarı noktaya dokunun — ayrıntısı burada görünür.</div>
    <div class="efsane">
      <span><i class="nis" style="background:#14110F;border-radius:50%"></i>${ROL==="misafir"?"Asıl sebep":"Kara Delik — sebep"}</span>
      <span><i class="nis" style="background:#fff;border-radius:50%;box-shadow:inset 0 0 0 1.5px #14110F,inset 0 0 0 3px #fff,inset 0 0 0 4.5px #14110F"></i>${ROL==="misafir"?"Dile gelen yan":"Ak Delik — şikâyet"}</span>
      <span><i class="nis" style="background:#F2B705;transform:rotate(45deg)"></i>${ROL==="misafir"?"Karar eşiği":"Berzah — karar"}</span>
      <span><i class="nis" style="background:#fff;border-radius:50%;box-shadow:inset 0 0 0 1.4px #14110F"></i>Çekici kütle</span>
      <span><i class="nis" style="background:#fff;border-radius:50%;box-shadow:inset 0 0 0 1.4px #E0301E"></i>İtici (retro)</span>
      <span><i class="nis" style="background:#F2B705;border-radius:50%"></i>${ROL==="misafir"?"Özel nokta":"Hesaplanan nokta"}</span>
      <span><i class="nis" style="background:#1B4FA0;border-radius:50%"></i>Paralel bağ</span>
      <span><i class="nis" style="background:#fff;border-radius:50%;box-shadow:inset 0 0 0 2px #8B5CF6"></i>${ROL==="misafir"?"Sınır dışı":"Hudûd dışı"}</span>
    </div>`;
}

/* Tam ekran: çark mobilde küçük kalıyordu ve katman düğmeleri sayfayı
   aşağı itiyordu. Büyütülünce çark ekranı kaplar, katmanlar üstte kalır. */
/* Yazdırma başlığı: çıktıda kimin haritası olduğu görünsün. */
function yazdir(){
  const g=(SON_ANALIZ&&SON_ANALIZ.girdi)||{};
  const b=$("yazdirBas");
  if(b)b.innerHTML=`<h1>${esc(g.ad||"Doğum haritası okuması")}</h1>
    <p>${esc(g.an||"")}${g.tz!=null?" · UTC"+(g.tz>=0?"+":"")+g.tz:""}
    ${g.ev_sistemi?" · ev sistemi "+esc(g.ev_sistemi):""}</p>`;
  window.print();
}

function tamEkranAc(){
  const eski=document.getElementById("tamPerde"); if(eski)eski.remove();
  document.body.insertAdjacentHTML("beforeend",
    `<div class="tam-perde" id="tamPerde" role="dialog" aria-modal="true" aria-label="Çark tam ekran">
       <button type="button" class="kapat" id="tamKapat" aria-label="Kapat">×</button>
       <div class="tam-ic" id="tamIc"></div>
     </div>`);
  const ic=document.getElementById("tamIc");
  ic.innerHTML=halkaCiz();
  document.body.style.overflow="hidden"; TAMEKRAN=true;
  document.getElementById("tamKapat").onclick=tamEkranKapat;
  document.getElementById("tamPerde").onclick=e=>{
    if(e.target.id==="tamPerde")tamEkranKapat();};
}
function tamEkranKapat(){
  const p=document.getElementById("tamPerde"); if(p)p.remove();
  document.body.style.overflow=""; TAMEKRAN=false;
}
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&TAMEKRAN)tamEkranKapat();});

function svgIndir(){
  const svg=document.querySelector("#halkaCizim svg");
  if(!svg)return;
  const kopya=svg.cloneNode(true);
  kopya.setAttribute("xmlns","http://www.w3.org/2000/svg");
  kopya.setAttribute("width","1000"); kopya.setAttribute("height","1000");
  // arka planı gömelim ki tek başına açıldığında doğru görünsün
  const zemin=document.createElementNS("http://www.w3.org/2000/svg","rect");
  zemin.setAttribute("width","400"); zemin.setAttribute("height","400");
  zemin.setAttribute("fill","#FFFFFF");
  kopya.insertBefore(zemin, kopya.firstChild);
  const metin='<?xml version="1.0" encoding="UTF-8"?>\n'+kopya.outerHTML;
  const a=document.createElement("a");
  const ad=(HALKA_SETI[HALKA_SECIM]||{}).ad||"harita";
  dosyaIndir(new Blob([metin],{type:"image/svg+xml"}),
             "zic-"+ad.replace(/\s+/g,"-").toLowerCase()+".svg", null);
}

function halkaBagla(){
  const si=$("svgIndir"); if(si)si.onclick=svgIndir;
  document.querySelectorAll(".halka-harita .ccark[data-c]").forEach(b=>b.onclick=()=>{
    CIFT=b.dataset.c;
    document.querySelectorAll(".halka-harita .ccark[data-c]").forEach(x=>
      x.classList.toggle("acik",x.dataset.c===CIFT));
    halkaYenile();
    const bi=document.getElementById("halkaBilgi");
    if(bi&&CIFT==="transit"&&TRANSIT)bi.innerHTML=
      `<b>Bugünkü gökyüzü</b> <span class="ince">${esc(TRANSIT.an||"")} · dış halkadaki mavi gliflere dokunun</span>`;
  });
  const te=document.getElementById("tamEkran");
  if(te)te.onclick=tamEkranAc;
  document.querySelectorAll(".halka-arac .katman").forEach(b=>b.onclick=()=>{
    HALKA_KATMAN[b.dataset.k]=!HALKA_KATMAN[b.dataset.k];
    b.classList.toggle("acik",HALKA_KATMAN[b.dataset.k]);
    halkaYenile();
  });
  // NOT: yalnız data-h taşıyanlar harita seçicidir. Çift çark düğmeleri
  // de aynı şeride konduğu için sınıfa göre bağlamak HALKA_SETI[NaN]
  // hatası üretiyordu.
  document.querySelectorAll(".halka-harita .harita[data-h]").forEach(b=>b.onclick=()=>{
    HALKA_SECIM=+b.dataset.h;
    HALKA_VERI=HALKA_SETI[HALKA_SECIM].v2;
    document.querySelectorAll(".halka-harita .harita[data-h]").forEach(x=>
      x.classList.toggle("acik",+x.dataset.h===HALKA_SECIM));
    const n=HALKA_SETI[HALKA_SECIM];
    const bilgi=document.getElementById("halkaBilgi");
    if(bilgi)bilgi.innerHTML=`<b>${esc(n.ad)}</b>`+(n.not?` <span class="ince">${esc(n.not)}</span>`:"")+
      `<br><span class="ince">Kara Delik ${esc(n.v2.KD.konum)} · Berzah ${esc((n.v2.berzah||{}).konum||"—")}</span>`;
    halkaYenile();
  });
  halkaYenile();
}

/* ============ yardımcılar ============ */
const kv=(k,v)=>`<div class="kv"><span>${esc(k)}</span><b>${esc(v)}</b></div>`;
function kart(baslik,satirlar,metin,usul){
  return `<div class="kart"><h3>${esc(baslik)}</h3>${satirlar||""}
    ${metin?`<p>${esc(metin)}</p>`:""}${usul?`<div class="usul">${esc(usul)}</div>`:""}</div>`;
}
function tablo(basliklar,satirlar){
  return `<div class="sarma"><table class="cizelge"><thead><tr>${
    basliklar.map(b=>`<th>${esc(b)}</th>`).join("")}</tr></thead><tbody>${
    satirlar.map(r=>`<tr>${r.map((c,i)=>`<td class="${i?"sayi":""}">${c}</td>`).join("")}</tr>`).join("")
  }</tbody></table></div>`;
}
const IMLER=[["im-daire","var(--kirmizi)"],["im-kare","var(--mavi)"],["im-ceyrek","var(--sari)"],
             ["im-daire","var(--turkuaz)"],["im-kare","var(--murekkep)"]];
function blok(no,baslik,ic,bolumId){
  // JS'te (-1)%5 = -1 olduğu için no<2 iken IMLER[-1] undefined dönüyordu.
  const nNum=(typeof no==="number")?no:2;
  const [sekil,renk]=IMLER[((nNum-2)%IMLER.length+IMLER.length)%IMLER.length];
  // v13'te yönetici Rasathanesi ölçüm yüzeyidir; ölçüme ayrıca AI metni
  // yazdırmak aynı bağlamı yeniden konuşturuyordu. AI yalnız Sahne görevlerinde.
  const dugme=(bolumId && ROL!=="yonetici")
    ? `<button class="ai-dugme" type="button" data-bolum="${esc(bolumId)}" data-baslik="${esc(baslik)}"
        title="Bu bölümü danışmana yorumlat" aria-label="${esc(baslik)} bölümünü AI ile yorumlat">
        <i></i><span class="uzun">AI analizi</span><span class="kisa">AI</span></button>`
    : "";
  const kat=bolumId?kategoriKodu(bolumId):"";
  const km=bolumId?kategoriBilgi(bolumId):null;
  const rozet=(ROL==="yonetici"&&km)
    ?`<span class="kategori-rozet" title="${esc(km.ac)}">${esc(km.ad)}</span>`:"";
  return `<section class="blok${kat?` kategori-${kat}`:""}"${bolumId?` data-kimlik="${esc(bolumId)}" data-kategori="${esc(kat)}"`:""}>
    <div class="blok-bas">
      <i class="im ${sekil}" style="background:${renk}"></i>
      ${ROL!=="yonetici"?`<span class="no">${String(no).padStart(2,"0")}</span>`:""}<h2>${esc(baslik)}</h2>
      ${rozet}${dugme}</div>${ic}</section>`;
}

/* ============ MODAL — bölüme özel AI analizi ============ */
let MODAL_ACIK=false;
function modalKapat(){
  const perde=document.getElementById("perde");
  if(perde)perde.remove();
  MODAL_ACIK=false;
  document.body.style.overflow="";
}
function modalAc(baslik){
  modalKapat();
  document.body.style.overflow="hidden"; MODAL_ACIK=true;
  document.body.insertAdjacentHTML("beforeend",`
    <div class="perde" id="perde">
      <div class="modal" role="dialog" aria-modal="true" aria-label="${esc(baslik)} analizi">
        <div class="modal-bas">
          <i></i>
          <div class="yaz"><div class="et">Bölüm analizi</div><h3>${esc(baslik)}</h3></div>
          <button class="kapat" id="modalKapat" aria-label="Kapat">×</button>
        </div>
        <div class="modal-govde" id="modalGovde">
          <span class="dusunuyor"><span class="yaziyor"><i></i><i></i><i></i></span>
          <span id="mDusun">Düşünüyorum…</span> <span class="sure" id="mSure">0 sn</span></span>
        </div>
        <div class="modal-alt">
          <span class="bilgi" id="modalBilgi">danışman çalışıyor</span>
          <button type="button" id="modalKopya">Kopyala</button>
        </div>
      </div>
    </div>`);
  document.getElementById("modalKapat").onclick=modalKapat;
  document.getElementById("perde").onclick=e=>{if(e.target.id==="perde")modalKapat();};
}
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&MODAL_ACIK)modalKapat();});

async function bolumAnalizi(bolumId,baslik){
  if(!SON_ANALIZ){alert("Önce analizi çalıştırın.");return;}
  modalAc(baslik);
  const t0=Date.now(); let adim=0;
  const sayac=setInterval(()=>{
    const d=$("mDusun"), su=$("mSure");
    if(!d){clearInterval(sayac);return;}
    const sn=Math.round((Date.now()-t0)/1000);
    if(sn>0&&sn%4===0)adim=(adim+1)%DUSUNME.length;
    d.textContent=(DUSUNME[adim%DUSUNME.length]||"Düşünüyorum")+"…"; su.textContent=sn+" sn";
  },1000);
  try{
    const r=await fetch("/api/v1/chat-bolum",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(OTURUM
        ?{bolum:bolumId,oturum:OTURUM,model:seciliModel()}
        :{bolum:bolumId,analiz:SON_ANALIZ,mod:SON_MOD,model:seciliModel()})});
    const d=await r.json();
    clearInterval(sayac);
    if(!$("modalGovde"))return;
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    $("modalGovde").innerHTML=md(d.yanit);
    $("modalBilgi").textContent=(seciliModel()||"varsayılan model")+" · "+
      Math.round((Date.now()-t0)/1000)+" sn";
    $("modalKopya").onclick=()=>{
      navigator.clipboard.writeText(d.yanit).then(()=>{
        $("modalKopya").textContent="Kopyalandı";
        setTimeout(()=>{const k=$("modalKopya"); if(k)k.textContent="Kopyala";},1600);
      });
    };
  }catch(err){
    clearInterval(sayac);
    if(!$("modalGovde"))return;
    $("modalGovde").innerHTML="<p style=\"color:var(--kirmizi)\">Analiz alınamadı: "+
      esc(kullaniciyaHata(err))+"</p><p>"+
      "Birazdan tekrar deneyin.</p>";
    $("modalBilgi").textContent="hata";
  }
}
/* Bölüm şeridi: mobilde 11 bölüm arasında tek dokunuşla geçiş. */
/* Katlanabilir bölümler: mobilde 17 bölüm 35 ekran boyu kaydırma demekti.
   Başlığa dokunmak açıp kapatır. Dar ekranda ilk bölüm ve danışman açık
   başlar, gerisi kapalı; geniş ekranda hepsi açık kalır (masaüstünde
   kaydırma sorun değil, kapalı başlamak orada engel olur). */
/* BÖLÜM HİYERARŞİSİ
   22 bölüm eşit ağırlıkta görünüyordu: Hüküm ile Chrono-Gravitron aynı
   boyutta, aynı sırada. Oysa bir seansta çoğunlukla üçü konuşuluyor.

   Hiçbir bölüm KALDIRILMADI ve hiçbir hesap silinmedi — yalnız hangisinin
   AÇIK BAŞLAYACAĞI değişti. Derin katmanlar kapalı başlar, başlığa
   dokununca açılır; "Derin katmanı aç" ile hepsi birden açılır. */
const BIRINCIL = ["omurga", "hukum", "sorular", "sentez", "sohbet"];

/* ---- KATEGORİ MİMARİSİ v12.9 ----
   Eski sürümde 25+ bölüm aynı uzun listede duruyordu. Artık her bölüm bir
   kategori ailesine bağlı. Hesap SİLİNMİYOR; yalnız yönetici çalışma akışı
   "hangi aileyi neden açıyorum?" sorusuna cevap veriyor. */
const KATEGORI_META={
  omurga:{ad:"MİZAN-5",kisa:"üst katman",ac:"Beş eksenli öncelik rotası"},
  cekirdek:{ad:"Çekirdek",kisa:"natal yapı",ac:"Hüküm, alan, çatal ve karar geometrisi"},
  zaman:{ad:"Zaman",kisa:"aktivasyon",ac:"Solar Return, yaş, lunasyon ve dönem pencereleri"},
  gerilim:{ad:"Gerilim",kisa:"dayanıklılık",ac:"Çelişki, direnç ve doğum saati hassasiyeti"},
  hareket:{ad:"Hareket",kisa:"eylem",ac:"Kabz/Bast, yakınsama, duraklama ve hamle"},
  mekan:{ad:"Mekân",kisa:"yer",ac:"Astrokartografi, hudûd ve şehir okumaları"},
  gelenek:{ad:"Gelenek & sembol",kisa:"destek",ac:"Kadim, deneme, Human Design ve spiritüel katman"},
  danisman:{ad:"Danışman",kisa:"çıktı",ac:"Sorular, formülasyon, sentez, rapor ve sohbet"},
  iliski:{ad:"İlişki",kisa:"iki harita",ac:"Sinastri, kompozit ve alan bindirmesi"}
};
const BOLUM_KATEGORI={
  omurga:"omurga",hukum:"cekirdek",halka:"cekirdek",catal:"cekirdek",
  kutleler:"cekirdek",kenarlar:"cekirdek",topoloji:"cekirdek",
  sira:"zaman",lunasyon:"zaman",donus:"zaman",esik:"zaman",sukut:"zaman",
  kabzbast:"hareket",yakinsama:"hareket",duraklama:"hareket",hamle:"hareket",
  sarsma:"gerilim",celiski:"gerilim",direnc:"gerilim",cevaplanabilirlik:"gerilim",guven:"gerilim",hamveri:"gerilim",
  zaman_ozet:"zaman",hareket_ozet:"hareket",
  hudud:"mekan",kartografi:"mekan",sehir:"mekan",
  deneme:"gelenek",kadim:"gelenek",hd:"gelenek",manevi:"gelenek",
  sorular:"danisman",formul:"danisman",sentez:"danisman",sohbet:"danisman",
  sinastri:"iliski",alanbukmesi:"iliski",kompozit:"iliski",davison:"iliski",deklinasyon:"iliski",iliski_solar:"iliski",kisi_a:"iliski",kisi_b:"iliski"
};
function kategoriKodu(bolumId){return BOLUM_KATEGORI[bolumId]||"cekirdek";}
function kategoriBilgi(bolumId){return KATEGORI_META[kategoriKodu(bolumId)]||KATEGORI_META.cekirdek;}

function yoneticiPanelKur(){
  const p=$("yoneticiMerkez"); if(!p)return;
  p.hidden=ROL!=="yonetici";
  const y=$("ymYeni");
  if(y&&!y.dataset.kuruldu){
    y.dataset.kuruldu="1";
    y.onclick=()=>{
      const b=$("modelKilidiAc");
      if(KILITLI_MODEL&&b&&b.offsetParent!==null)b.click();
      $("form").scrollIntoView({behavior:"smooth",block:"start"});
    };
  }
  const s=$("ymSonuca");
  if(s&&!s.dataset.kuruldu){s.dataset.kuruldu="1";s.onclick=()=>{
    if(typeof sahneGoster==="function")sahneGoster("hukum");
    const el=$("sahneKabuk")||$("sonuc"); if(el)el.scrollIntoView({behavior:"smooth",block:"start"});
  };}
  const k=$("ymKritik");
  if(k&&!k.dataset.kuruldu){k.dataset.kuruldu="1";k.onclick=()=>{
    if(typeof sahneGoster==="function")sahneGoster("rasathane");
    kategoriFiltrele("rota");
    const el=$("sonuc"); if(el)el.scrollIntoView({behavior:"smooth",block:"start"});
  };}
}

function yoneticiPanelGuncelle(d){
  if(ROL!=="yonetici")return;
  yoneticiPanelKur();
  const o=(d&&d.oruntu_omurgasi)||{};
  const ai=(d&&d.ai)||{};
  const solar=(d&&d.solar_v2)||null;
  if($("ymDurum"))$("ymDurum").innerHTML=`<i></i><span>${d?"Analiz hazır":"Yeni analiz bekleniyor"}</span>`;
  if($("ymOturum"))$("ymOturum").textContent=(d&&d.oturum)?String(d.oturum).slice(0,10)+"…":"—";
  if($("ymModel"))$("ymModel").textContent=ai.model||KILITLI_MODEL||seciliModel()||"seçilmedi";
  if($("ymModelAlt"))$("ymModelAlt").textContent=(ai.locked||KILITLI_MODEL)?"oturuma kilitli":"analiz başında kilitlenir";
  if($("ymSolar"))$("ymSolar").textContent=solar&&!solar.hata?`SR ${solar.yil}`:"Natal";
  if($("ymSaglik"))$("ymSaglik").textContent=o.hazir_kategori!=null?`${o.hazir_kategori}/${o.toplam_kategori}`:"—";
  if($("ymSonuca"))$("ymSonuca").disabled=!d;
  if($("ymKritik"))$("ymKritik").disabled=!d||!o.rota;
}

function mizan5Blogu(d){
  const o=(d||{}).oruntu_omurgasi||{};
  if(!o||o.hata||!Array.isArray(o.eksenler))return "";
  const eks=o.eksenler.map(e=>`<article class="m5-eksen" data-eksen="${esc(e.kod)}">
      <div class="m5-eksen-bas"><span>${esc(e.ad)}</span><b>${esc(e.puan)}</b></div>
      <div class="m5-yol"><i style="width:${Math.max(0,Math.min(100,+e.puan||0))}%"></i></div>
      <p>${esc(e.ozet||"")}</p>
      <div class="m5-kaynak">${(e.kaynaklar||[]).slice(0,5).map(k=>`<span>${esc(k.ad)} <b>${esc(k.deger)}</b></span>`).join("")}</div>
    </article>`).join("");
  const rota=(o.rota||[]).map(r=>`<button type="button" class="m5-rota" data-kat="${esc(r.kod)}">
      <span>${esc(r.sira)} · ${esc(r.ad)}</span><b>${esc(r.puan)}</b></button>`).join("");
  return blok("M5","MİZAN-5 · Örüntü Omurgası",`
    <div class="m5-hero">
      <div><span class="m5-kicker">Yeni üst katman</span><h3>${esc((o.rota&&o.rota[0]&&o.rota[0].ad)||"Öncelik")} ekseni önde</h3>
      <p>${esc(o.okuma||"")}</p></div>
      <div class="m5-saglik"><strong>${esc(o.hazir_kategori||0)}/${esc(o.toplam_kategori||0)}</strong><span>kategori ailesi hazır</span></div>
    </div>
    <div class="m5-grid">${eks}</div>
    <div class="m5-alt"><div><span class="etiket">Okuma rotası</span><div class="m5-rota-list">${rota}</div></div>
      <p class="ipucu">${esc(o.sinir||"")}</p></div>`,"omurga");
}

function kategoriSinyalBloklari(d){
  if(ROL!=="yonetici")return "";
  const yas=d.yas_katmani||{}, kz=d.kayip_zaman||{}, hp=d.hamle_penceresi||{},
        yk=d.yakinsama||{}, sr=d.sarsma||{}, cv=d.cevaplanabilirlik||{},
        tm=d.temas_acisi||{}, solar=d.solar_v2||null;
  const enHam=Object.values(hp.en_iyi||{}).sort((a,b)=>(+b.puan||0)-(+a.puan||0))[0]||null;
  const yak=(yk.cekirdek||[])[0]||null;
  const guclu=(cv.guclu||[]).slice(0,4), zayif=(cv.zayif||[]).slice(0,4);
  const grp=sr.gruplar||{};
  let H="";
  H+=blok("Z","Zaman omurgası",`<div class="sinyal-grid">
      <div class="sinyal-kart"><span>Yıllık katman</span><strong>${solar&&!solar.hata?`SR ${esc(solar.yil)}`:"Yalnız Natal"}</strong><p>${solar&&!solar.hata?"Yıllık aktivasyon Hüküm ve MİZAN-5 içinde çalışıyor.":"Solar Return bağlandığında bu aile yeniden hesaplanır."}</p></div>
      <div class="sinyal-kart"><span>Yaş eşiği</span><strong>${esc(yas.esik_sayisi!=null?yas.esik_sayisi:"—")}</strong><p>${esc(yas.okuma||"Yaş katmanı üretilemedi.")}</p></div>
      <div class="sinyal-kart"><span>Sessiz / yoğun yaşlar</span><strong>${esc((kz.sessiz_yaslar||[]).slice(0,3).join(", ")||"—")}</strong><p>${esc((kz.yogun_yaslar||[]).length?`Yoğun: ${kz.yogun_yaslar.slice(0,3).join(", ")}`:(kz.okuma||"—"))}</p></div>
      <div class="sinyal-kart"><span>Yakın hamle</span><strong>${esc(enHam?enHam.ad:"—")}</strong><p>${enHam?`${esc(enHam.basla)} – ${esc(enHam.bitis)} · puan ${esc(enHam.puan)}`:"Hamle penceresi yok."}</p></div>
    </div><p class="ipucu">Bu özet zamanlamayı tek hükme indirgemez; Solar Return, yaş, yaşam döngüsü ve haftalık pencereyi aynı ailede görünür kılar.</p>`,"zaman_ozet");
  H+=blok("H","Hareket rotası",`<div class="sinyal-grid sinyal-grid-3">
      <div class="sinyal-kart"><span>Yakınsama çekirdeği</span><strong>${esc(yak?yak.ad:"Tek merkez yok")}</strong><p>${yak?`${esc(yak.kaynak_turu)} bağımsız katman · ${esc(yak.kanit_sayisi)} kanıt`:esc(yk.okuma||"Katmanlar tek eksende birleşmiyor.")}</p></div>
      <div class="sinyal-kart"><span>Önerilen hareket</span><strong>${esc(enHam?enHam.ad:"—")}</strong><p>${esc(hp.okuma||"Hamle katmanı üretilemedi.")}</p></div>
      <div class="sinyal-kart"><span>Yapısal sürtünme</span><strong>${esc((hp.yapisal_notlar||[]).length)}</strong><p>${esc((hp.yapisal_notlar||[])[0]||"Belirgin ek yapısal not yok.")}</p></div>
    </div><p class="ipucu">Yakınsama neyin tekrarlandığını, Hamle Penceresi ise aynı yapıyla hangi hareketin daha az sürtünme ürettiğini gösterir.</p>`,"hareket_ozet");
  H+=blok("G","Güven & dayanıklılık",`<div class="sinyal-grid sinyal-grid-3">
      <div class="sinyal-kart"><span>Sarsma sağlamlığı</span><strong>${sr.saglamlik!=null?`%${Math.round((+sr.saglamlik||0)*100)}`:"—"}</strong><p>${esc(sr.okuma||"Saat hassasiyeti ölçülemedi.")}</p></div>
      <div class="sinyal-kart"><span>Konuşulabilir alanlar</span><strong>${esc(guclu.length?guclu.join(" · "):"—")}</strong><p>${zayif.length?`Az yaslan: ${esc(zayif.join(" · "))}`:esc(cv.okuma||"—")}</p></div>
      <div class="sinyal-kart"><span>Aktarım kanalı</span><strong>${tm.temas_sayisi!=null?`${esc(tm.temas_sayisi)} temas`:"Tanımlı değil"}</strong><p>${esc((tm.uyarilar||[])[0]?.metin||tm.okuma||"Danışman haritası tanımlıysa temas açısı burada görünür.")}</p></div>
    </div><div class="sinyal-mini"><span>±5 dk kırılan: <b>${esc((grp.kum||[]).length)}</b></span><span>±15 dk kırılgan: <b>${esc((grp["kırılgan"]||[]).length)}</b></span><span>Güçlü cevap alanı: <b>${esc((cv.guclu||[]).length)}</b></span></div>`,"guven");
  return H;
}

function kategoriMerkeziKur(d){
  if(ROL!=="yonetici")return;
  const sonuc=$("sonuc"); if(!sonuc)return;
  const eski=$("kategoriMerkezi"); if(eski)eski.remove();
  const mevcut=new Set([...sonuc.querySelectorAll(".blok[data-kategori]")].map(x=>x.dataset.kategori));
  if(mevcut.size<2)return;
  const o=(d||SON_ANALIZ||{}).oruntu_omurgasi||{};
  const rota=new Set((o.rota||[]).slice(0,2).map(x=>x.kod));
  const hub=document.createElement("div"); hub.id="kategoriMerkezi"; hub.className="kategori-merkezi";
  const dugmeler=[`<button type="button" class="etkin" data-k="hepsi"><b>Tümü</b><span>çalışma alanı</span></button>`];
  Object.entries(KATEGORI_META).forEach(([kod,m])=>{
    if(kod==="omurga"||!mevcut.has(kod))return;
    dugmeler.push(`<button type="button" data-k="${esc(kod)}"><b>${esc(m.ad)}</b><span>${esc(m.kisa)}</span></button>`);
  });
  if(rota.size)dugmeler.splice(1,0,`<button type="button" class="rota" data-k="rota"><b>Öncelik rotası</b><span>ilk iki eksen</span></button>`);
  hub.innerHTML=`<div class="km-bas"><div><span class="etiket">Kategori görünümü</span><strong>Tek liste yerine çalışma kümeleri</strong></div>
      <span class="km-not">${rota.size?"MİZAN-5 ilk iki ekseni işaretledi":"Kategori seçerek sadeleştirin"}</span></div>
      <div class="km-dugmeler">${dugmeler.join("")}</div>`;
  const nav=$("gezinme");
  if(nav&&nav.parentNode===sonuc)nav.insertAdjacentElement("afterend",hub); else sonuc.insertAdjacentElement("afterbegin",hub);
  hub.querySelectorAll("button[data-k]").forEach(b=>b.onclick=()=>kategoriFiltrele(b.dataset.k));
  sonuc.querySelectorAll(".m5-rota").forEach(b=>b.onclick=()=>kategoriFiltrele(b.dataset.kat));
}

function kategoriFiltrele(kod){
  if(ROL!=="yonetici")return;
  const sonuc=$("sonuc"); if(!sonuc)return;
  const o=(SON_ANALIZ||{}).oruntu_omurgasi||{};
  let izin=null;
  if(kod==="rota")izin=new Set((o.rota||[]).slice(0,2).map(x=>x.kod).concat(["omurga","danisman"]));
  else if(kod!=="hepsi")izin=new Set([kod,"omurga"]);
  sonuc.querySelectorAll('.blok[data-kategori]').forEach(bl=>{
    const giz=!!izin&&!izin.has(bl.dataset.kategori);
    bl.classList.toggle("kategori-gizli",giz);
  });
  const km=$("kategoriMerkezi"); if(km)km.querySelectorAll('button[data-k]').forEach(b=>b.classList.toggle("etkin",b.dataset.k===kod));
  const nav=$("gezinme"); if(nav)nav.querySelectorAll('a').forEach(a=>{
    const h=$(a.getAttribute('href').slice(1));
    a.classList.toggle('kategori-gizli',!!(h&&h.classList.contains('kategori-gizli')));
  });
}

/* ---- YAN İÇİNDEKİLER ----
   21 bölüm tek uzun sütun. Nerede olduğunu görmek ve atlamak için. */
function icindekilerKur(){
  if(ROL==="yonetici")return;
  const sonuc=$("sonuc"); if(!sonuc||$("icindekiler"))return;
  const bloklar=[...sonuc.querySelectorAll(".blok")];
  if(bloklar.length<6)return;
  const nav=document.createElement("nav");
  nav.id="icindekiler"; nav.className="icindekiler";
  nav.innerHTML='<div class="ic-bas">Bölümler</div><ol></ol>';
  const ol=nav.querySelector("ol");
  bloklar.forEach((bl,i)=>{
    const h=bl.querySelector(".blok-bas h2");
    if(!h)return;
    if(!bl.id)bl.id="blok-"+i;
    const li=document.createElement("li");
    li.innerHTML=`<a href="#${bl.id}">${esc(h.textContent.split("·")[0].trim())}</a>`;
    li.querySelector("a").onclick=(e)=>{
      e.preventDefault();
      bl.classList.remove("kapali");
      [...bl.children].filter(c=>!c.classList.contains("blok-bas"))
        .forEach(c=>c.style.display="");
      const bas=bl.querySelector(".blok-bas");
      if(bas)bas.setAttribute("aria-expanded","true");
      bl.scrollIntoView({behavior:"smooth",block:"start"});
    };
    ol.appendChild(li);
  });
  sonuc.parentNode.insertBefore(nav,sonuc);
  // hangi bölümdeyiz
  const izle=new IntersectionObserver((girisler)=>{
    girisler.forEach(g=>{
      const i=bloklar.indexOf(g.target);
      const li=ol.children[i];
      if(li)li.classList.toggle("etkin",g.isIntersecting);
    });
  },{rootMargin:"-20% 0px -70% 0px"});
  bloklar.forEach(b=>izle.observe(b));
}

/* ---- SUNUM KİPİ ----
   Danışana ekran gösterirken: büyük yazı, tek sütun, çeldirici yok. */
/* ---- TEK GİRİŞ ÇUBUĞU ----
   AI'ye sekiz ayrı kapı vardı: chat, bölüm, sentez, formül, soru, manevi,
   şehir, rapor. Seansta "hangisine basayım" diye düşünmek istemezsin.
   Buradan yazdığın metin, içeriğine göre doğru yüzeye yönlendirilir.
   Sekiz kapı bire iner; hepsi çalışmaya devam eder. */
const YONLENDIRME=[
  {yuzey:"sehir",   desen:/\b(taşın|göç|yerleş|şehir|ülke|nerede yaşa|hangi şehir)\w*/i},
  {yuzey:"manevi",  desen:/\b(tefekkür|manev|ruhsal|vefk|dua|zikir|kapı(lar)?|gelenek)\w*/i},
  {yuzey:"soru",    desen:/\b(rızk|geçim|kariyer|meslek|iş kur|evlen|eş|ilişki|çocuk|sağlık|para|yatırım|ne zaman)\w*/i},
  {yuzey:"sentez",  desen:/\b(özetle|bütün|genel|toparla|hepsini)\w*/i},
];
function yuzeySec(metin){
  for(const y of YONLENDIRME) if(y.desen.test(metin)) return y.yuzey;
  return "chat";
}

function girisCubuguKur(){
  if($("tekCubuk"))return;
  const d=document.createElement("div");
  d.id="tekCubuk"; d.className="tek-cubuk";
  d.innerHTML=`<input id="tekSoru" placeholder="Ne sormak istersiniz? — sistem doğru yere yönlendirir"
      autocomplete="off" aria-label="Soru">
    <button type="button" id="tekGonder">Sor</button>`;
  document.body.appendChild(d);
  const gonder=async()=>{
    const q=$("tekSoru").value.trim(); if(!q)return;
    if(!SON_ANALIZ){ $("tekSoru").value=""; $("tekSoru").placeholder="Önce analiz çalıştırın"; return; }
    const yuzey=yuzeySec(q);
    $("tekSoru").value="";
    // ilgili bölüme götür ve oradaki alanı doldur
    const hedefler={chat:["#soru","#gonder","Danışman"],
                    soru:["#soruEk","#soruBtn","Danışan soruları"],
                    manevi:["#mSoru","#mGonder","Spiritüel"],
                    sehir:["#sSoru","#sGonder","Yer"],
                    sentez:[null,"#sentezBtn","Bütünsel"]};
    const [alan,dugme,baslik]=hedefler[yuzey]||hedefler.chat;
    const blok=[...document.querySelectorAll(".blok")]
      .find(b=>(b.querySelector(".blok-bas h2")||{}).textContent?.includes(baslik));
    if(blok){
      blok.classList.remove("kapali");
      [...blok.children].filter(c=>!c.classList.contains("blok-bas"))
        .forEach(c=>c.style.display="");
      blok.scrollIntoView({behavior:"smooth",block:"start"});
    }
    await new Promise(r=>setTimeout(r,450));
    if(alan&&$(alan.slice(1)))$(alan.slice(1)).value=q;
    const b=$(dugme.slice(1));
    if(b&&!b.disabled)b.click();
  };
  $("tekGonder").onclick=gonder;
  $("tekSoru").addEventListener("keydown",e=>{ if(e.key==="Enter")gonder(); });
}

function sunumKur(){
  if($("sunumBtn"))return;
  const d=document.createElement("button");
  d.id="sunumBtn"; d.type="button"; d.className="sunum-dugme";
  d.textContent="Sunum kipi";
  d.setAttribute("aria-pressed","false");
  d.onclick=()=>{
    const acik=document.body.classList.toggle("sunum");
    d.setAttribute("aria-pressed",acik?"true":"false");
    d.textContent=acik?"Sunumdan çık":"Sunum kipi";
  };
  const y=document.querySelector(".ust-serit")||document.querySelector(".serlevha");
  if(y)y.appendChild(d);
}

function derinBaslik(){
  if(ROL==="yonetici")return;
  const sonuc = $("sonuc");
  if(!sonuc || $("derinAyrac")) return;
  const bloklar = [...sonuc.querySelectorAll(".blok")];
  const ilkDerin = bloklar.find(bl => {
    const k = bl.dataset.kimlik || "";
    return k && !BIRINCIL.includes(k);
  });
  if(!ilkDerin) return;
  const sayi = bloklar.filter(bl =>
    bl.dataset.kimlik && !BIRINCIL.includes(bl.dataset.kimlik)).length;
  const ayrac = document.createElement("div");
  ayrac.className = "derin-ayrac";
  ayrac.id = "derinAyrac";
  ayrac.innerHTML = `<span class="derin-et">Derin katman · ${sayi} bölüm</span>
    <button type="button" id="derinAc">Hepsini aç</button>`;
  ilkDerin.parentNode.insertBefore(ayrac, ilkDerin);
  $("derinAc").onclick = () => {
    const kapaliVar = bloklar.some(bl => bl.dataset.kimlik &&
      !BIRINCIL.includes(bl.dataset.kimlik) && bl.classList.contains("kapali"));
    bloklar.forEach(bl => {
      const k = bl.dataset.kimlik;
      if(!k || BIRINCIL.includes(k)) return;
      const bas = bl.querySelector(".blok-bas");
      const govde = [...bl.children].filter(c => !c.classList.contains("blok-bas"));
      bl.classList.toggle("kapali", !kapaliVar);
      if(bas) bas.setAttribute("aria-expanded", kapaliVar ? "true" : "false");
      govde.forEach(c => c.style.display = kapaliVar ? "" : "none");
    });
    $("derinAc").textContent = kapaliVar ? "Hepsini kapat" : "Hepsini aç";
  };
}

function katlamaKur(){
  const bloklar=[...document.querySelectorAll("#sonuc .blok")];
  bloklar.forEach((bl,i)=>{
    const bas=bl.querySelector(".blok-bas");
    if(!bas||bas.dataset.katlanir)return;
    bas.dataset.katlanir="1";
    bas.setAttribute("role","button");
    bas.setAttribute("tabindex","0");
    const govde=[...bl.children].filter(c=>!c.classList.contains("blok-bas"));
    // Yönetici görünümünde MİZAN-5'in ilk iki ekseni başlangıçta açık.
    // Böylece kategori filtresi yalnız renk değiştiren bir süs değil, gerçek çalışma rotasıdır.
    const kimlik = bl.dataset.kimlik || "";
    const rotaK=new Set((((SON_ANALIZ||{}).oruntu_omurgasi||{}).rota||[]).slice(0,2).map(x=>x.kod));
    let kapali = !!kimlik && !BIRINCIL.includes(kimlik);
    if(ROL==="yonetici" && (rotaK.has(bl.dataset.kategori)||bl.dataset.kategori==="iliski")) kapali=false;
    const uygula=(k)=>{
      bl.classList.toggle("kapali",k);
      bas.setAttribute("aria-expanded", k?"false":"true");
      govde.forEach(c=>c.style.display = k?"none":"");
    };
    uygula(kapali);
    const cevir=(e)=>{
      // başlıktaki AI düğmesine dokunmak katlamayı tetiklemesin
      if(e.target.closest(".ai-btn"))return;
      uygula(!bl.classList.contains("kapali"));
    };
    bas.addEventListener("click",cevir);
    bas.addEventListener("keydown",e=>{
      if(e.key==="Enter"||e.key===" "){e.preventDefault();cevir(e);}
    });
  });
}

function tumunuAc(ac){
  document.querySelectorAll("#sonuc .blok").forEach(bl=>{
    const bas=bl.querySelector(".blok-bas"); if(!bas)return;
    const govde=[...bl.children].filter(c=>!c.classList.contains("blok-bas"));
    bl.classList.toggle("kapali",!ac);
    bas.setAttribute("aria-expanded",ac?"true":"false");
    govde.forEach(c=>c.style.display = ac?"":"none");
  });
}

function gezinmeKur(){
  const eski=document.getElementById("gezinme"); if(eski)eski.remove();
  const bloklar=[...document.querySelectorAll("#sonuc .blok")];
  if(bloklar.length<3)return;
  const ogeler=bloklar.map((bl,i)=>{
    const kimlik="bolum-"+i; bl.id=kimlik;
    const h2=bl.querySelector(".blok-bas h2");
    const no=bl.querySelector(".blok-bas .no");
    const ad=(h2?h2.textContent:"Bölüm").split("·")[0].trim();
    return `<a href="#${kimlik}" data-i="${i}">${no?no.textContent+" ":""}${esc(ad)}</a>`;
  }).join("");
  $("sonuc").insertAdjacentHTML("afterbegin",
    `<nav class="gezinme" id="gezinme" aria-label="Bölümler">
       <div class="gezinme-ic">${ogeler}</div>
       <button type="button" class="hepsi" id="hepsiBtn" aria-label="Tüm bölümleri aç veya kapat">Tümünü aç</button>
     </nav>`);
  const hb=document.getElementById("hepsiBtn");
  if(hb)hb.onclick=()=>{
    const acik=hb.textContent.startsWith("Tümünü aç");
    tumunuAc(acik);
    hb.textContent=acik?"Tümünü kapat":"Tümünü aç";
  };
  const baglar=[...document.querySelectorAll("#gezinme a")];
  baglar.forEach(a=>a.addEventListener("click",e=>{
    e.preventDefault();
    const h=document.getElementById(a.getAttribute("href").slice(1));
    if(h)h.scrollIntoView({behavior:"smooth",block:"start"});
  }));
  // görünen bölümü şeritte işaretle ve şeridi ona kaydır
  if(window.IntersectionObserver){
    const go=new IntersectionObserver(girisler=>{
      girisler.forEach(g=>{
        if(!g.isIntersecting)return;
        const i=bloklar.indexOf(g.target); if(i<0)return;
        baglar.forEach(a=>a.classList.toggle("etkin",+a.dataset.i===i));
        const et=baglar[i];
        if(et)et.parentElement.scrollTo({left:et.offsetLeft-60,behavior:"smooth"});
      });
    },{rootMargin:"-56px 0px -70% 0px",threshold:0});
    bloklar.forEach(bl=>go.observe(bl));
  }
}

function yukariKur(){
  if(document.getElementById("yukariBtn"))return;
  document.body.insertAdjacentHTML("beforeend",
    `<button class="yukari" id="yukariBtn" type="button" aria-label="Başa dön">↑</button>`);
  const b=document.getElementById("yukariBtn");
  b.onclick=()=>window.scrollTo({top:0,behavior:"smooth"});
  window.addEventListener("scroll",()=>b.classList.toggle("gorunur",window.scrollY>700),
                          {passive:true});
}

async function dinamikTara(){
  const btn=$("dinBtn"), kutu=$("dinSonuc");
  if(!btn||!SON_ANALIZ)return;
  btn.disabled=true; const eski=btn.textContent; btn.textContent="Taranıyor…";
  kutu.innerHTML=`<div class="dusunuyor" style="margin-top:14px">
    <span class="yaziyor"><i></i><i></i><i></i></span> Alan zaman içinde yeniden hesaplanıyor…</div>`;
  try{
    const g=girdiTopla(); g.yil=parseInt($("dinYil").value)||24;
    const r=await fetch("/api/v1/dinamik",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    const y=d.yuruyen_berzah;
    SON_ANALIZ.yuruyen_berzah=y;      // AI bağlamına da girsin
    if(y.hata)throw new Error(y.hata);
    const cat=(y.catallanmalar||[]);
    kutu.innerHTML=`<div class="kartlar" style="margin-top:18px">
      ${kart("Yörünge",kv("Aralık",y.baslangic+" → "+y.bitis)+
        kv("Natal Berzah",y.natal_berzah||"—")+
        kv("Ortalama hız",y.ortalama_hiz_derece_ay+" °/ay · "+y.hiz_dilimi)+
        kv("Gezilen burçlar",(y.gezilen_burclar||[]).join(", "))+
        kv("Gezilen evler",(y.gezilen_evler||[]).join(", "))+
        kv("Natalden azami sapma",(y.natalden_azami_sapma??"—")+"°"),y.okuma)}
      ${kart("Çatallanmalar",cat.length?cat.map(c=>
          kv(c.tarih,c.tur.split("—")[0].trim()+" · "+c.konum)).join("")
        :"<p>Bu ufukta çatallanma yok — seçenek sayısı sabit kalıyor.</p>",
        cat.length?"Açılma: yeni bir seçenek belirdi. Kapanma: bir seçenek ortadan kalktı; artık tek yol var.":null)}
      ${kart("Eşik yörüngesi",(y.yorunge||[]).slice(0,8).map(p=>
        kv(p.tarih,p.konum+" · "+p.ev+". ev")).join(""),null,y.yontem)}
    </div>`;
  }catch(err){
    kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">Tarama tamamlanamadı. ${esc(kullaniciyaHata(err))}</p>`;
  }finally{btn.disabled=false;btn.textContent=eski;}
}

function aiDugmeleriBagla(){
  document.querySelectorAll("#sonuc .ai-dugme").forEach(b=>
    b.onclick=()=>bolumAnalizi(b.dataset.bolum,b.dataset.baslik));
}

/* ============ BÜTÜNSEL SENTEZ ============ */
/* Her bölüm kendi başına doğru ama hiçbiri diğerini bilmiyor. Sentez, bir
   danışmanın seans sonunda yaptığı şeyi yapar: hepsini tek hikâyeye bağlar
   ve çelişkileri açıkça söyler. İstek üzerine üretilir (kota disiplini). */
/* ---- Formülasyon ---- */
let FORMUL_KATMAN=[], FORMUL_METNI="", FORMUL_GECMIS=[];
(async function formulKatmanYukle(){
  try{
    const r=await fetch("/api/v1/formul-katmanlar");
    FORMUL_KATMAN=(await r.json()).katmanlar||[];
  }catch(e){ FORMUL_KATMAN=[]; }
})();

/* ---- YER SORGUSU ---- 34.695 şehirlik veri zaten yüklü; buradan seçilen
   yer için hem çözümleme hem o yere ÖZEL sohbet açılır. */
let SEHIR_SON=null, SEHIR_GECMIS=[];
/* ---- Spiritüel çalışmalar ---- */
let MANEVI_GECMIS=[];
/* ---- Danışan soruları ---- */
let SORU_KATALOG=null, SORU_KATEGORI=null;
async function soruKur(){
  const sek=$("soruSekme"), lst=$("soruListe");
  if(!sek)return;
  try{
    if(!SORU_KATALOG){
      const r=await fetch("/api/v1/sorular");
      SORU_KATALOG=await r.json();
    }
  }catch(e){ sek.innerHTML='<p class="ipucu">Soru listesi alınamadı.</p>'; return; }
  const kat=SORU_KATALOG.kategoriler||[];
  SORU_KATEGORI=SORU_KATEGORI||(kat[0]&&kat[0].kod);
  sek.innerHTML=kat.map(k=>
    `<button type="button" data-k="${esc(k.kod)}"
      aria-pressed="${k.kod===SORU_KATEGORI}">${esc(k.ad)}</button>`).join("");
  const ciz=()=>{
    lst.innerHTML=(SORU_KATALOG.sorular||[])
      .filter(s=>s.kategori===SORU_KATEGORI)
      .map(s=>`<label class="kutucuk"><input type="checkbox" value="${esc(s.kod)}">
        <span>${esc(s.metin)}${s.hassas?' <em class="hassas-not">· çerçeveli</em>':''}</span></label>`).join("");
  };
  sek.querySelectorAll("button").forEach(b=>b.onclick=()=>{
    SORU_KATEGORI=b.dataset.k;
    sek.querySelectorAll("button").forEach(x=>
      x.setAttribute("aria-pressed", x.dataset.k===SORU_KATEGORI));
    ciz();
  });
  ciz();

  // seçim sayısı bütün kategorilerde toplanır
  const secili=()=>SORU_SECIM;
  lst.addEventListener("change",e=>{
    const k=e.target.value;
    if(e.target.checked){ if(!SORU_SECIM.includes(k))SORU_SECIM.push(k); }
    else SORU_SECIM=SORU_SECIM.filter(x=>x!==k);
    guncelle();
  });
  const guncelle=()=>{
    const n=SORU_SECIM.length, b=$("soruBtn");
    b.textContent = n===0 ? "Soru seçin ya da kendi sorunuzu yazın"
                  : n>4 ? "En fazla 4 soru — fazlası tek turda yetişmiyor" : `${n} soruyu cevapla`;
    b.disabled = n>4;
  };
  guncelle();

  $("soruBtn").onclick=async()=>{
    const ek=$("soruEk").value.trim();
    if(!SORU_SECIM.length && !ek){
      $("soruSonuc").innerHTML='<p class="ipucu" style="color:var(--kirmizi)">En az bir soru seçin ya da kendi sorunuzu yazın.</p>';
      return;
    }
    const b=$("soruBtn"), kutu=$("soruSonuc"), eski=b.textContent;
    b.disabled=true; b.textContent="Cevaplanıyor…";
    kutu.innerHTML=`<div class="dusunuyor" style="margin-top:16px">
      <span class="yaziyor"><i></i><i></i><i></i></span><span>Düşünüyorum…</span></div>`;
    try{
      const g=Object.assign({kodlar:SORU_SECIM,ek_soru:ek,rol:ROL,model:seciliModel()},
        OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
      const r=await fetch("/api/v1/soru-cevap",{method:"POST",
        headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
      const d=await r.json();
      if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
      kutu.innerHTML=`<div class="sentez-metin">${md(d.yanit)}</div>
        <button type="button" class="indir" id="soruKopya" style="margin-top:14px">Kopyala</button>`;
      $("soruKopya").onclick=e=>panoyaKopyala(d.yanit,e.target);
    }catch(e){
      kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
    }finally{ b.disabled=false; b.textContent=eski; }
  };
}
let SORU_SECIM=[];

/* ---- TAM RAPOR (PDF) ----
   On bölüm TEK TEK istenir. Tek istekte üretmek mümkün değil: gerçek
   modelde bölüm başına ~40 sn, toplam ~400 sn eder ve vekil koparır.
   Bölüm bölüm gitmek hem sınırın altında kalır hem ilerleme gösterir. */
let RAPOR_BOLUMLERI=[], RAPOR_TUR="";

async function raporBolumYenile(sira,tur){
  const el=document.querySelector(`.rapor-bolum[data-sira="${sira}"]`);
  if(!el)return;
  const govde=el.querySelector(".rapor-bolum-govde");
  const eski=govde.innerHTML;
  govde.innerHTML='<span class="yaziyor"><i></i><i></i><i></i></span>';
  try{
    const onceki=RAPOR_BOLUMLERI.slice(0,sira)
      .map(b=>`[${b.baslik}] ${String(b.metin).slice(0,tur==="anlatim"?520:200)}`).join("\n");
    const g=Object.assign({sira:sira,tur:tur,onceki:onceki.slice(-3200),model:seciliModel()},
      OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
    const r=await fetch("/api/v1/rapor-bolum",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    govde.innerHTML=md(d.metin);
    if(RAPOR_BOLUMLERI[sira]) RAPOR_BOLUMLERI[sira]={baslik:d.baslik,metin:d.metin};
    oturumYedekle();
  }catch(e){
    govde.innerHTML=eski+`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
  }
}

/* ---- ANINDA ARAMA ----
   Danışan bir şey söylüyor ve senin O AN bilmen gereken şey "bu haritada
   var mı, nerede?" Şu an bunun için sohbete yazıp beklemek gerekiyordu.

   AĞA HİÇ GİTMEZ: bölümlerin ekrandaki metni üzerinde çalışır. Jeton
   harcamaz, beklemez, hata veremez. */
function aramaKur(){
  if($("aramaKutu")) return;
  const bloklar=[...document.querySelectorAll("#sonuc .blok")];
  if(bloklar.length<4) return;
  const k=document.createElement("div");
  k.id="aramaKutu"; k.className="arama-kutu";
  k.innerHTML=`<input id="aramaGirdi" type="search" autocomplete="off"
      placeholder="Haritada ara — sabotaj, erteleme, sınır, para…">
    <div class="arama-sonuc" id="aramaSonuc"></div>`;
  document.body.appendChild(k);
  const dizin=bloklar.map((bl,i)=>{
    if(!bl.id) bl.id="blok"+i;
    const h=bl.querySelector(".blok-bas h2");
    return {id:bl.id, ad:h?h.textContent.split("·")[0].trim():("Bölüm "+(i+1)),
            metin:(bl.innerText||"").toLowerCase()};
  });
  const giris=$("aramaGirdi"), sonuc=$("aramaSonuc");
  let zaman=null;
  giris.addEventListener("input",()=>{
    clearTimeout(zaman);
    zaman=setTimeout(()=>{
      const q=giris.value.trim().toLowerCase();
      if(q.length<3){ sonuc.innerHTML=""; sonuc.classList.remove("acik"); return; }
      const bulunan=dizin.map(x=>{
        let n=0,p=0;
        while((p=x.metin.indexOf(q,p))!==-1){ n++; p+=q.length; }
        if(!n) return null;
        const i=x.metin.indexOf(q), bas=Math.max(0,i-46);
        return {ad:x.ad,id:x.id,n:n,
                parca:"…"+x.metin.slice(bas,i+q.length+56).trim()+"…"};
      }).filter(Boolean).sort((a,b)=>b.n-a.n).slice(0,6);
      if(!bulunan.length){
        sonuc.innerHTML='<div class="arama-bos">Bu haritada geçmiyor.</div>';
      }else{
        sonuc.innerHTML=bulunan.map(x=>
          `<button type="button" data-id="${x.id}">
             <span class="ad">${esc(x.ad)} <i>${x.n}×</i></span>
             <span class="parca">${esc(x.parca)}</span></button>`).join("");
        sonuc.querySelectorAll("button").forEach(b=>b.onclick=()=>{
          const t=document.getElementById(b.dataset.id);
          if(!t) return;
          if(t.classList.contains("kapali")){
            const bs=t.querySelector(".blok-bas"); if(bs)bs.click();
          }
          t.scrollIntoView({behavior:"smooth",block:"start"});
          sonuc.classList.remove("acik"); giris.value="";
        });
      }
      sonuc.classList.add("acik");
    },140);
  });
  document.addEventListener("keydown",e=>{
    if(e.key==="Escape"){ sonuc.classList.remove("acik"); giris.blur(); }
    if((e.ctrlKey||e.metaKey)&&e.key==="k"){ e.preventDefault(); giris.focus(); }
  });
}

/* ---- LUNASYON TAKVİMİ ---- */
let LUN_TAKVIM=null;
function lunasyonKur(){
  const b=$("lunBtn"); if(!b)return;
  b.onclick=async()=>{
    const kutu=$("lunSonuc"), eski=b.textContent;
    b.disabled=true; b.textContent="Hesaplanıyor…";
    try{
      const gi=girdiTopla();
      const sv=(SON_ANALIZ&&SON_ANALIZ.solar_v2)||null;
      if(sv&&!sv.hata&&sv.yil)gi.sr_year=+sv.yil; else delete gi.sr_year;
      const r=await fetch("/api/v1/lunasyon",{method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({dogum:gi,ay_sayisi:12})});
      const d=await r.json();
      if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
      LUN_TAKVIM=d;
      lunCiz(d);
    }catch(e){
      kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
    }finally{ b.disabled=false; b.textContent=eski; }
  };
}

function lunCiz(d){
  const kutu=$("lunSonuc");
  const simge={"yeni ay":"●","dolunay":"○","güneş tutulması":"◆","ay tutulması":"◇"};
  const bh=(d.bu_hafta||{});
  const satir=(o,i)=>`
    <button type="button" class="lun-satir${o.agirlik>=4?" agir":""}" data-i="${i}">
      <span class="lun-tar">${esc(o.tarih)}</span>
      <span class="lun-tur">${simge[o.tur]||"•"} ${esc(o.tur)}${o.cesit?" · "+esc(o.cesit):""}</span>
      <span class="lun-ev">${o.natal_ev?o.natal_ev+". alan":"—"}${
        o.solar_ev&&o.solar_ev!==o.natal_ev?`<i class="lun-sol">yıl ${o.solar_ev}.</i>`:""}</span>
      <span class="lun-tem">${o.temaslar.length?esc(o.temaslar[0].nokta+" "+o.temaslar[0].aci):"—"}</span>
      <span class="lun-ag">${o.agirlik}</span>
    </button>`;
  kutu.innerHTML=`
    ${bh.yaklasan&&bh.yaklasan.length?`<div class="lun-yakin">
      <span class="et">Yaklaşan</span>
      <p>${esc(bh.okuma||"")}</p></div>`:""}
    <div class="lun-baslik">
      <span>Tarih</span><span>Olay</span><span>Alan</span><span>Temas</span><span>Ağırlık</span>
    </div>
    <div class="lun-liste">${(d.olaylar||[]).map(satir).join("")}</div>
    <p class="ipucu">${esc(d.uyari||"")}</p>
    <div id="lunOkuma"></div>`;
  kutu.querySelectorAll(".lun-satir").forEach(x=>
    x.onclick=()=>lunOku(+x.dataset.i));
}

async function lunOku(i){
  if(!LUN_TAKVIM)return;
  const o=(LUN_TAKVIM.olaylar||[])[i]; if(!o)return;
  const kutu=$("lunOkuma");
  kutu.innerHTML=`<div class="dusunuyor" style="margin-top:14px">
    <span class="yaziyor"><i></i><i></i><i></i></span>
    <span>${esc(o.tarih)} ${esc(o.tur)} okunuyor…</span></div>`;
  try{
    const g=Object.assign({dogum:o,rol:ROL,model:seciliModel()},
      OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
    const r=await fetch("/api/v1/lunasyon-okuma",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    const bag=o.bag||{}, kats=(bag.kategoriler||[]);
    LUN_SECILI=o; LUN_SOHBET=[];
    kutu.innerHTML=`<div class="lun-okuma">
      <div class="lun-okuma-bas">${esc(o.tarih)} · ${esc(o.tur)}
        ${o.natal_ev?" · natal "+o.natal_ev+". alan":""}
        ${o.solar_ev?" · yıl "+o.solar_ev+". alan":""}</div>
      ${kats.length?`<div class="lun-kats"><span class="et">Bu olay şu bölümleri uyandırıyor</span>
        <div class="lun-rozet">${kats.map(k=>`<span>${esc(k.ad)}</span>`).join("")}</div></div>`:""}
      ${(o.oneriler||[]).length?`<div class="lun-oneri"><span class="et">Sistemin önerileri</span>
        <ul>${o.oneriler.map(x=>`<li>${esc(x)}</li>`).join("")}</ul></div>`:""}
      <div class="sentez-metin">${md(d.yanit)}</div>
      <div class="formul-sohbet" id="lunSohbetKut">
        <div class="akis" id="lAkis"></div>
        <div class="giris-satir">
          <input id="lSoru" placeholder="Bu olay üzerine sorun…" autocomplete="off">
          <button type="button" class="gonder" id="lGonder">Sor</button>
        </div>
      </div>
    </div>`;
    $("lGonder").onclick=()=>lunSor($("lSoru").value.trim());
    $("lSoru").addEventListener("keydown",e=>{if(e.key==="Enter")lunSor($("lSoru").value.trim());});
    kutu.scrollIntoView({behavior:"smooth",block:"nearest"});
  }catch(e){
    kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
  }
}

let LUN_SECILI=null, LUN_SOHBET=[];
async function lunSor(soru){
  if(!soru||!LUN_SECILI)return;
  $("lSoru").value="";
  LUN_SOHBET.push({rol:"kullanici",metin:soru});
  $("lAkis").insertAdjacentHTML("beforeend",
    `<div class="balon ben"><div class="govde">${esc(soru)}</div></div>`);
  $("lAkis").insertAdjacentHTML("beforeend",
    `<div class="balon ai" id="lBekle"><div class="govde"><span class="yaziyor"><i></i><i></i><i></i></span></div></div>`);
  $("lAkis").scrollTop=$("lAkis").scrollHeight;
  try{
    const g=Object.assign({dogum:LUN_SECILI,soru:soru,
      gecmis:LUN_SOHBET.slice(0,-1),rol:ROL,model:seciliModel()},
      OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
    const r=await fetch("/api/v1/lunasyon-sohbet",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    const w=$("lBekle"); if(w)w.remove();
    LUN_SOHBET.push({rol:"danisman",metin:d.yanit});
    $("lAkis").insertAdjacentHTML("beforeend",
      `<div class="balon ai"><div class="govde">${md(d.yanit)}</div></div>`);
    $("lAkis").scrollTop=$("lAkis").scrollHeight;
  }catch(e){
    const w=$("lBekle"); if(w)w.remove();
    $("lAkis").insertAdjacentHTML("beforeend",
      `<div class="balon ai"><div class="govde"><p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p></div></div>`);
  }
}

/* ---- SÜKÛT HARİTASI ---- */
let SK_HARITA=null;
function sukutKur(){
  const b=$("skBtn"); if(!b)return;
  b.onclick=async()=>{
    const kutu=$("skSonuc"), eski=b.textContent;
    b.disabled=true; b.textContent="Hesaplanıyor…";
    try{
      const gi=referansDogum();
      const r=await fetch("/api/v1/sukut",{method:"POST",
        headers:{"Content-Type":"application/json"},body:JSON.stringify({dogum:gi,analiz:SON_ANALIZ||{}})});
      const d=await r.json();
      if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
      SK_HARITA=d; skCiz(d);
    }catch(e){
      kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
    }finally{ b.disabled=false; b.textContent=eski; }
  };
}

function skCiz(d){
  const kutu=$("skSonuc");
  const e=d.egri||[], enb=d.en_yuksek||1, ens=d.en_dusuk||0;
  const yuk=(v)=>Math.round(((v-ens)/Math.max(.001,enb-ens))*100);
  const sessiz=(t)=>(d.sukut_araliklari||[]).some(a=>a.basla<=t&&t<=a.bitis);
  const sikis=(t)=>(d.sikisma_araliklari||[]).some(a=>a.basla<=t&&t<=a.bitis);
  const cubuk=e.map(x=>{
    const s=sessiz(x.tarih)?" sessiz":(sikis(x.tarih)?" sikis":"");
    return `<i class="sk-c${s}" style="height:${Math.max(3,yuk(x.basinc))}%"
      title="${esc(x.tarih)} · ${x.basinc}"></i>`;}).join("");
  const aralik=(a,tur)=>`<button type="button" class="sk-aralik ${tur}" data-t="${esc(a.basla)}">
      <span class="sk-tar">${esc(a.basla)} – ${esc(a.bitis)}</span>
      <span class="sk-gun">${a.gun} gün</span>
      <span class="sk-ort">${tur==="sessiz"?"ort "+a.ortalama:"tepe "+a.tepe}</span>
    </button>`;
  kutu.innerHTML=`
    <div class="sk-ozet">
      <div><span class="et">Sessiz</span><b>${d.sukut_gun} gün</b>
        <i>%${Math.round((d.sukut_orani||0)*100)}</i></div>
      <div><span class="et">Basınç</span><b>${d.en_dusuk} – ${d.en_yuksek}</b>
        <i>ort ${d.ortalama_basinc}</i></div>
      <div><span class="et">Aralık</span><b>${(d.sukut_araliklari||[]).length} sessiz</b>
        <i>${(d.sikisma_araliklari||[]).length} sıkışık</i></div>
    </div>
    <div class="sk-egri">${cubuk}</div>
    <div class="sk-lejant"><i class="sk-c sessiz"></i> sessiz
      <i class="sk-c"></i> olağan <i class="sk-c sikis"></i> sıkışık</div>
    <p class="ipucu"><b>Doku:</b> ${esc(d.doku||"")}</p>
    ${(d.sukut_araliklari||[]).length?`<div class="sk-liste"><span class="et">Sessiz aralıklar</span>
      ${d.sukut_araliklari.map(a=>aralik(a,"sessiz")).join("")}</div>`:""}
    ${(d.sikisma_araliklari||[]).length?`<div class="sk-liste"><span class="et">Sıkışık aralıklar</span>
      ${d.sikisma_araliklari.map(a=>aralik(a,"sikis")).join("")}</div>`:""}
    <div class="sk-sorgu">
      <span class="et">Yanlışlama sorgusu</span>
      <p class="ipucu" style="margin:4px 0 8px">Danışan bir dönemden şikâyet
        ediyorsa tarihi girin: o dönem sessizse sebep gökyüzü değildir.</p>
      <div class="giris-satir">
        <input id="skTarih" type="date" style="max-width:190px">
        <button type="button" class="gonder" id="skSor">Sorgula</button>
      </div>
      <div id="skCevap"></div>
    </div>
    <p class="ipucu">${esc(d.uyari||"")}</p>
    <button type="button" class="hesapla" id="skOku" style="margin-top:14px">Bunu yorumla</button>
    <div id="skOkuma"></div>`;
  kutu.querySelectorAll(".sk-aralik").forEach(x=>x.onclick=()=>{
    $("skTarih").value=x.dataset.t; skSorgula();
  });
  $("skSor").onclick=skSorgula;
  $("skOku").onclick=skYorumla;
}

async function skSorgula(){
  const t=$("skTarih").value, k=$("skCevap");
  if(!t||!SK_HARITA)return;
  try{
    const gi=(SON_ANALIZ&&SON_ANALIZ.girdi)||{};
    const r=await fetch("/api/v1/sukut",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({dogum:gi,soru:t})});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    const s=d.sorgu||{};
    k.innerHTML=`<div class="sk-cevap ${esc(s.durum||"")}">
      <b>${esc(t)} · ${esc((s.durum||"").toUpperCase())}</b>
      <p>${esc(s.okuma||"")}</p></div>`;
  }catch(e){
    k.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
  }
}

async function skYorumla(){
  const b=$("skOku"), kutu=$("skOkuma");
  if(!SK_HARITA)return;
  b.disabled=true;
  kutu.innerHTML=`<div class="dusunuyor" style="margin-top:14px">
    <span class="yaziyor"><i></i><i></i><i></i></span><span>Düşünüyorum…</span></div>`;
  try{
    const g=Object.assign({dogum:SK_HARITA,rol:ROL,model:seciliModel()},
      OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
    const r=await fetch("/api/v1/sukut-okuma",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    kutu.innerHTML=`<div class="sentez-metin">${md(d.yanit)}</div>`;
  }catch(e){
    kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
  }finally{ b.disabled=false; }
}

/* ---- ALGI EŞİĞİ ---- */
let ES_VERI=null;
function esikKur(){
  const b=$("esBtn"); if(!b)return;
  b.onclick=async()=>{
    const kutu=$("esSonuc"), eski=b.textContent;
    b.disabled=true; b.textContent="Hesaplanıyor…";
    try{
      const gi=referansDogum();
      const r=await fetch("/api/v1/esik",{method:"POST",
        headers:{"Content-Type":"application/json"},body:JSON.stringify({dogum:gi,analiz:SON_ANALIZ||{}})});
      const d=await r.json();
      if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
      ES_VERI=d; esCiz(d);
    }catch(e){
      kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
    }finally{ b.disabled=false; b.textContent=eski; }
  };
}

function esCiz(d){
  const k=d.orb_karsilastirma||{};
  const fark=d.orb_farki||0;
  $("esSonuc").innerHTML=`
    <div class="es-ozet">
      <div class="es-buyuk">
        <span class="et">Bu haritanın orbu</span>
        <b>${d.turetilmis_orb}°</b>
        <i>geleneksel ${d.geleneksel_orb}° · ${fark>0?"+":""}${fark}°</i>
      </div>
      <div><span class="et">Eşik</span><b>${d.esik_kat}×</b>
        <i>${esc(d.seviye||"")}</i></div>
      <div><span class="et">Taban gürültü</span><b>${d.taban_gurultu}</b>
        <i>oynaklık ${d.oynaklik_orani}</i></div>
    </div>
    <div class="es-olcek">
      <div class="es-bar"><span style="left:${Math.min(96,Math.max(2,(d.turetilmis_orb/7)*100))}%"
        class="es-im turetilmis" title="bu harita ${d.turetilmis_orb}°"></span>
        <span style="left:${(3/7)*100}%" class="es-im gelenek" title="geleneksel 3°"></span></div>
      <div class="es-etiket"><span>1°</span><span>dar</span><span>geniş</span><span>7°</span></div>
    </div>
    <p class="ipucu"><b>Okuma:</b> ${esc(d.okuma||"")}</p>
    <div class="es-danisman"><span class="et">Danışmana</span>
      <p>${esc(d.danismana||"")}</p></div>
    ${k.okuma?`<p class="ipucu">${esc(k.okuma)}</p>`:""}
    ${(k.sinirdakiler||[]).length?`<div class="es-sinir"><span class="et">Sınırdaki açılar</span>
      ${k.sinirdakiler.map(x=>`<div class="es-satir ${esc(x.durum||"")}">
        <span>${esc(x.a)} <i>${esc(x.aci)}</i> ${esc(x.b)}</span>
        <span class="es-orb">${x.orb}°</span>
        <span class="es-dur">${esc(x.durum||"")}</span></div>`).join("")}</div>`:""}
    <p class="ipucu">${esc(d.sinir||"")}</p>
    <button type="button" class="hesapla" id="esOku" style="margin-top:14px">Bunu yorumla</button>
    <div id="esOkuma"></div>`;
  $("esOku").onclick=esYorumla;
}

async function esYorumla(){
  const b=$("esOku"), kutu=$("esOkuma");
  if(!ES_VERI)return;
  b.disabled=true;
  kutu.innerHTML=`<div class="dusunuyor" style="margin-top:14px">
    <span class="yaziyor"><i></i><i></i><i></i></span><span>Düşünüyorum…</span></div>`;
  try{
    const g=Object.assign({dogum:ES_VERI,rol:ROL,model:seciliModel()},
      OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
    const r=await fetch("/api/v1/esik-okuma",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    kutu.innerHTML=`<div class="sentez-metin">${md(d.yanit)}</div>`;
  }catch(e){
    kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
  }finally{ b.disabled=false; }
}

/* ---- DÖNÜŞ NOKTASI ---- */
function donusKur(){
  const b=$("dnBtn"); if(!b)return;
  b.onclick=async()=>{
    const kutu=$("dnSonuc"), eski=b.textContent;
    b.disabled=true; b.textContent="Taranıyor…";
    kutu.innerHTML=`<div class="dusunuyor" style="margin-top:12px">
      <span class="yaziyor"><i></i><i></i><i></i></span>
      <span>Dört yavaş gezegen, kırk yıl ileri taranıyor…</span></div>`;
    try{
      const gi=referansDogum();
      const r=await fetch("/api/v1/donus-noktasi",{method:"POST",
        headers:{"Content-Type":"application/json"},body:JSON.stringify({dogum:gi,analiz:SON_ANALIZ||{}})});
      const d=await r.json();
      if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
      const sat=(k,son)=>`<div class="dn-satir${son?" son":""}">
        <span class="dn-gok">${esc(k.gok)}</span>
        <span class="dn-aci">${esc(k.aci)}</span>
        <span class="dn-nok">${esc(k.nokta)}</span>
        <span class="dn-tar">${son?esc(k.son||"—"):esc(k.sonraki||"—")}</span>
        <span class="dn-yas">${son?(k.son_yas??"—"):(k.sonraki_yas??"—")} yaş</span>
      </div>`;
      kutu.innerHTML=`
        <div class="dn-ozet"><b>${d.toplam}</b> kapı tarandı</div>
        ${(d.yaklasan||[]).length?`<div class="dn-grup"><span class="et">Yaklaşan kapılar</span>
          ${d.yaklasan.map(k=>sat(k,false)).join("")}</div>`:""}
        ${(d.kapanmis||[]).length?`<div class="dn-grup kapali"><span class="et">Bir daha gelmeyecek</span>
          ${d.kapanmis.map(k=>sat(k,true)).join("")}</div>`:""}
        <p class="ipucu"><b>Okuma:</b> ${esc(d.okuma||"")}</p>
        <p class="ipucu">${esc(d.sinir||"")}</p>`;
    }catch(e){
      kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
    }finally{ b.disabled=false; b.textContent=eski; }
  };
}

/* ---- SEANS KİPİ ----
   Sorun tema değil DÜZEN'di: 23 bölüm TEKNİK ADINA göre dizili
   (Hüküm, Alan halkası, Hudûd-ı Felek…). Danışan karşındayken hangi
   tekniğin ne tuttuğunu hatırlamak gerekiyor.

   Aynı veri SEANSIN ANINA göre yeniden diziliyor. Teknik bölümler
   kaybolmuyor — "Tüm katmanlar" ile geri geliyor. */
const SEANS_ADIMLAR=[["acilis","Açılış","bu kişi kim"],
  ["dinlerken","Dinlerken","söylediği nerede"],
  ["soylerken","Söylerken","ne açar, ne kapatır"],
  ["kapanirken","Kapanırken","ne zaman ne yapmalı"]];

function seansKur(){
  if($("seansKutu")||!SON_ANALIZ) return;
  const s=$("sonuc"); if(!s) return;
  const k=document.createElement("div");
  k.id="seansKutu";
  k.innerHTML=`<div class="seans-serit" id="seansSerit">${
    SEANS_ADIMLAR.map((a,i)=>`<button type="button" data-a="${a[0]}"
      class="${i===0?"etkin":""}"><b>${a[1]}</b>${esc(a[2])}</button>`).join("")
  }</div><div id="seansIcerik"></div>`;
  s.parentNode.insertBefore(k,s);
  seansCiz("acilis");
  k.querySelectorAll(".seans-serit button").forEach(b=>b.onclick=()=>{
    k.querySelectorAll(".seans-serit button").forEach(x=>
      x.classList.toggle("etkin",x===b));
    seansCiz(b.dataset.a);
  });
}

function seansCiz(adim){
  const d=SON_ANALIZ||{}, ic=$("seansIcerik"); if(!ic)return;
  const yk=d.yakinsama||{},cv=d.cevaplanabilirlik||{},dr=d.direnc||[],
        sr=d.sarsma||{},hp=d.hamle_penceresi||{},ce=d.celiskiler||[],
        v2=d.berzah_v2||{},ber=v2.berzah||{},ya=d.yas_katmani||{};
  let H="";
  if(adim==="acilis"){
    const c=(yk.cekirdek||[])[0];
    if(c)H+=`<div class="seans-cekirdek"><span class="et">Bu haritanın omurgası</span>
      <p>${esc(c.ad)} — ${c.kaynak_turu} bağımsız katman aynı yeri gösteriyor.</p></div>`;
    H+=`<div class="seans-ikili">
      <div class="seans-kutu"><h4>Neyle gelecek</h4><p>${esc((v2.AD||{}).konum||"—")} ·
        ${(v2.AD||{}).ev||"?"}. alan. Şikâyet buradan çıkar.</p></div>
      <div class="seans-kutu"><h4>Asıl mesele</h4><p>${esc((v2.KD||{}).konum||"—")} ·
        ${(v2.KD||{}).ev||"?"}. alan. Kaynak burada.</p></div></div>
      <div class="seans-bas">Çatal</div><div class="seans-kutu">
      <p><b>${esc(ber.catalin_cumlesi||"—")}</b></p>
      <p>Yanlış refleks: ${esc(ber.yanlis_refleks||"—")}</p>
      <p>Hamle: ${esc(ber.berzah_hamlesi||"—")}</p></div>`;
    if(ya.okuma)H+=`<div class="seans-bas">Yaşın yükü</div>
      <div class="seans-kutu"><p>${esc(ya.okuma)}</p></div>`;
  } else if(adim==="dinlerken"){
    H+=`<div class="seans-bas">Danışan bir şey söyledi — haritada nerede?</div>
      <div class="seans-arama"><input id="seansAra" type="search" autocomplete="off"
        placeholder="Bir kelime yazın — sabotaj, erteleme, para, sınır…">
        <div class="arama-sonuc" id="seansAraSonuc"></div></div>`;
    if(ce.length){H+=`<div class="seans-bas">Çelişkiler — tek cevap verme</div>`;
      ce.forEach(c=>{H+=`<div class="seans-kutu"><h4>${esc(c.baslik)}</h4>
        <p>${esc(c.bir_yan)}</p><p><i>Buna karşılık:</i> ${esc(c.obur_yan)}</p></div>`;});}
  } else if(adim==="soylerken"){
    if(dr.length){H+=`<div class="seans-bas">Ne kapatır, ne açar</div>`;
      dr.forEach(r=>{H+=`<div class="seans-ikili" style="margin-bottom:12px">
        <div class="seans-kutu kapatir"><h4>${esc(r.ne_zaman)}</h4><p>${esc(r.kapatir)}</p></div>
        <div class="seans-kutu acar"><h4>Bunun yerine</h4><p>${esc(r.acar)}</p></div></div>`;});}
    const g=(cv.alanlar||[]).filter(a=>a.seviye==="güçlü"),
          z=(cv.alanlar||[]).filter(a=>a.seviye==="zayıf");
    H+=`<div class="seans-bas">Nerede konuş, nerede sus</div><div class="seans-ikili">
      <div class="seans-kutu acar"><h4>Açık konuş</h4><ul>${
        g.map(a=>`<li>${esc(a.ad)}</li>`).join("")||"<li>—</li>"}</ul></div>
      <div class="seans-kutu kapatir"><h4>Az söyle</h4><ul>${
        z.slice(0,4).map(a=>`<li>${esc(a.ad)}</li>`).join("")||"<li>—</li>"}</ul></div></div>`;
    if((sr.gruplar||{}).kum&&sr.gruplar.kum.length)
      H+=`<div class="seans-bas">Saat kesin değilse söyleme</div>
        <div class="seans-kutu kapatir"><p>${esc(sr.gruplar.kum.join(", "))} —
        beş dakikalık hata bunları değiştiriyor.</p></div>`;
  } else {
    if(hp.en_iyi){H+=`<div class="seans-bas">Hangi hafta hangi hamle</div>
      <div class="seans-kutu"><div class="seans-hamle">${
        Object.values(hp.en_iyi).map(e=>`<b>${esc(e.ad)}</b>
          <span>${esc(e.basla)} – ${esc(e.bitis)}</span>`).join("")}</div></div>`;
      if((hp.yapisal_notlar||[]).length)H+=`<div class="seans-kutu kapatir"
        style="margin-top:12px"><h4>Yapısal zorluk</h4>${
        hp.yapisal_notlar.map(n=>`<p>${esc(n)}</p>`).join("")}</div>`;}
    H+=`<div class="seans-bas">Bu hafta tek adım</div><div class="seans-kutu">
      <p>${esc(ber.berzah_hamlesi||"—")} — bitince "yaptım" denebilecek
      kadar küçük bir hâlini seçin.</p></div>`;
  }
  H+=`<div class="seans-tumu"><button type="button" class="hesapla" id="seansTumu">
    Tüm katmanlar (${document.querySelectorAll("#sonuc .blok").length} bölüm)</button></div>`;
  ic.innerHTML=H;
  const t=$("seansTumu");
  if(t)t.onclick=()=>{document.documentElement.classList.remove("seans");
    const k=$("seansKutu");if(k)k.remove();
    const b=$("seansBtn");if(b)b.textContent="Seans kipi";};
  if($("seansAra"))seansAramaKur();
}

function seansAramaKur(){
  const g=$("seansAra"),so=$("seansAraSonuc");
  const bl=[...document.querySelectorAll("#sonuc .blok")].map((b,i)=>{
    if(!b.id)b.id="blok"+i;
    const h=b.querySelector(".blok-bas h2");
    return {id:b.id,ad:h?h.textContent.split("·")[0].trim():"Bölüm "+(i+1),
            metin:(b.innerText||"").toLowerCase()};});
  let z=null;
  g.addEventListener("input",()=>{clearTimeout(z);z=setTimeout(()=>{
    const q=g.value.trim().toLowerCase();
    if(q.length<3){so.innerHTML="";so.classList.remove("acik");return;}
    const bul=bl.map(x=>{let n=0,p=0;
      while((p=x.metin.indexOf(q,p))!==-1){n++;p+=q.length;}
      if(!n)return null;
      const i=x.metin.indexOf(q),b=Math.max(0,i-40);
      return {ad:x.ad,id:x.id,n,parca:"…"+x.metin.slice(b,i+q.length+60).trim()+"…"};
    }).filter(Boolean).sort((a,b)=>b.n-a.n).slice(0,5);
    so.innerHTML=bul.length?bul.map(x=>`<button type="button" data-id="${x.id}">
      <span class="ad">${esc(x.ad)} <i>${x.n}×</i></span>
      <span class="parca">${esc(x.parca)}</span></button>`).join("")
      :'<div class="arama-bos">Bu haritada geçmiyor.</div>';
    so.querySelectorAll("button").forEach(b=>b.onclick=()=>{
      document.documentElement.classList.remove("seans");
      const k=$("seansKutu");if(k)k.remove();
      const t=document.getElementById(b.dataset.id);
      if(t){if(t.classList.contains("kapali")){
        const bs=t.querySelector(".blok-bas");if(bs)bs.click();}
        t.scrollIntoView({behavior:"smooth",block:"start"});}});
    so.classList.add("acik");},140);});
}

function seansDugmesi(){
  if($("seansBtn"))return;
  const b=document.createElement("button");
  b.id="seansBtn";b.className="sunum-dugme";b.type="button";
  b.style.bottom="118px";b.textContent="Seans kipi";
  b.title="Teknik bölümler yerine seansın anına göre düzen (Alt+S)";
  document.body.appendChild(b);
  const ac=()=>{const v=document.documentElement.classList.toggle("seans");
    if(v){seansKur();b.textContent="Seanstan çık";window.scrollTo({top:0});}
    else{const k=$("seansKutu");if(k)k.remove();b.textContent="Seans kipi";}};
  b.onclick=ac;
  document.addEventListener("keydown",e=>{
    if(e.altKey&&!e.ctrlKey&&!e.metaKey&&(e.key||"").toLowerCase()==="s"){
      e.preventDefault();ac();}});
}

function raporKur(){
  [$("raporBtn"), $("raporBtn2")].filter(Boolean).forEach(b => b.onclick = () => raporUret(b));
  if($("raporPdfBtn"))$("raporPdfBtn").onclick=()=>raporPdfIndir();
  if(RAPOR_BOLUMLERI.length)raporCiz();
}

/* Bölüm bittikçe ekranda görünür: sen okurken sonraki yazılır.
   Bekleme ölü zaman olmaktan çıkar, ve yanlış giden bölüm baştan
   yazdırılabilir — önceden ya hepsi ya hiçbiri vardı. */
function raporCiz(){
  const kutu=$("raporMetin"); if(!kutu)return;
  if(!RAPOR_BOLUMLERI.length){ kutu.innerHTML=""; return; }
  kutu.innerHTML=RAPOR_BOLUMLERI.map((b,i)=>`
    <div class="rapor-bolum">
      <div class="rapor-bolum-bas">
        <h4>${esc(b.baslik)}</h4>
        <button type="button" class="ccark" data-yeniden="${i}">Yeniden yaz</button>
      </div>
      <div class="sentez-metin">${md(b.metin)}</div>
    </div>`).join("");
  kutu.querySelectorAll("[data-yeniden]").forEach(d=>
    d.onclick=()=>raporBolumYenile(+d.dataset.yeniden));
  if($("raporPdfKut"))$("raporPdfKut").style.display=RAPOR_BOLUMLERI.length?"flex":"none";
}

async function raporUret(b){
  const tur=b.dataset.tur||"danisan";
  const kutu=$("raporDurum"), eski=b.textContent;
  b.disabled=true;
  if(RAPOR_TUR!==tur){ RAPOR_BOLUMLERI=[]; RAPOR_TUR=tur; raporCiz(); }
  const ciz=(i,n,ad)=>{
    kutu.innerHTML=`<div class="rapor-ilerleme">
      <div class="cubuk"><div style="width:${Math.round(i/n*100)}%"></div></div>
      <span>${i}/${n} · ${esc(ad||"")}</span></div>`;
  };
  let i=RAPOR_BOLUMLERI.length, toplam=10;
  ciz(i,toplam,"başlıyor");
  try{
    while(i<toplam){
      b.textContent=`Bölüm ${i+1}…`;
      let ozet=RAPOR_BOLUMLERI.map(x=>`[${x.baslik}] ${x.metin.slice(0,tur==="anlatim"?520:200)}`).join("\n");
      const g=Object.assign({sira:i,tur:tur,onceki:ozet.slice(tur==="anlatim"?-3200:-2200),
        model:seciliModel()}, OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
      const r=await fetch("/api/v1/rapor-bolum",{method:"POST",
        headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
      const d=await r.json();
      if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
      toplam=d.toplam||toplam;
      RAPOR_BOLUMLERI.push({baslik:d.baslik,metin:d.metin});
      i++; ciz(i,toplam,d.baslik);
      raporCiz();                    // bittikçe göster
      oturumYedekle();               // her bölüm yedeklenir
      if(d.son)break;
    }
    kutu.innerHTML=`<p class="ipucu">${RAPOR_BOLUMLERI.length} bölüm hazır.
      Aşağıdan okuyabilir, beğenmediğinizi yeniden yazdırabilir,
      sonra PDF alabilirsiniz.</p>`;
  }catch(e){
    const n=RAPOR_BOLUMLERI.length;
    kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">
      ${esc(kullaniciyaHata(e))}${n?` — ${n} bölüm yazıldı, kaybolmadı.
      Düğmeye tekrar basarsanız kaldığı yerden devam eder.`:""}</p>`;
  }finally{ b.disabled=false; b.textContent=eski; }
}

async function raporBolumYenile(i){
  if(!RAPOR_BOLUMLERI[i])return;
  const kutu=$("raporDurum");
  kutu.innerHTML=`<div class="dusunuyor"><span class="yaziyor"><i></i><i></i><i></i></span>
    <span>${esc(RAPOR_BOLUMLERI[i].baslik)} yeniden yazılıyor…</span></div>`;
  try{
    const ozet=RAPOR_BOLUMLERI.filter((_,j)=>j<i)
      .map(x=>`[${x.baslik}] ${x.metin.slice(0,300)}`).join("\n");
    const g=Object.assign({sira:i,tur:RAPOR_TUR||"danisan",onceki:ozet.slice(-2400),
      model:seciliModel()}, OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
    const r=await fetch("/api/v1/rapor-bolum",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    RAPOR_BOLUMLERI[i]={baslik:d.baslik,metin:d.metin};
    raporCiz(); oturumYedekle();
    kutu.innerHTML=`<p class="ipucu">${esc(d.baslik)} yenilendi.</p>`;
  }catch(e){
    kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
  }
}

async function raporPdfIndir(){
  if(!RAPOR_BOLUMLERI.length)return;
  const b=$("raporPdfBtn"), eski=b.textContent;
  b.disabled=true; b.textContent="PDF kuruluyor…";
  try{
    const gi=(SON_ANALIZ&&SON_ANALIZ.girdi)||{};
    const r=await fetch("/api/v1/rapor-pdf",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({bolumler:RAPOR_BOLUMLERI,tur:RAPOR_TUR||"danisan",
        ad:gi.ad||"Danışan",
        alt:(gi.an||"")+(gi.ev_sistemi?" · ev sistemi "+gi.ev_sistemi:"")})});
    if(!r.ok){ let d={}; try{d=await r.json();}catch(e){}
      throw new Error(sunucuHatasi(d,r.status)); }
    // `kutu` bu kapsamda TANIMSIZDI: dosyaIndir çağrısı ReferenceError
    // atıyor, catch'e düşüyor ve kullanıcı hiçbir şey görmüyordu.
    // Sessiz hatanın ta kendisi — "PDF kaydet dedim, bir şey olmadı".
    const blob=await r.blob();
    const dosyaAdi=((gi.ad||"rapor").replace(/[^\wçğıöşüÇĞİÖŞÜ -]/g,"").trim()||"rapor")+
      (RAPOR_TUR==="anlatim"?" anlatim.pdf":" okuma.pdf");
    dosyaIndir(blob, dosyaAdi, $("raporDurum"));
  }catch(e){
    $("raporDurum").innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
  }finally{ b.disabled=false; b.textContent=eski; }
}

function maneviKur(){
  const b=$("mnBtn"); if(!b)return;
  const kutu=$("mnSonuc");
  const cagir=async(soru)=>{
    if(soru){
      $("mSoru").value="";
      MANEVI_GECMIS.push({rol:"kullanici",metin:soru});
      $("mAkis").insertAdjacentHTML("beforeend",
        `<div class="balon ben"><div class="govde">${esc(soru)}</div></div>`);
      $("mAkis").insertAdjacentHTML("beforeend",
        `<div class="balon ai" id="mBekle"><div class="govde"><span class="yaziyor"><i></i><i></i><i></i></span></div></div>`);
      $("mAkis").scrollTop=$("mAkis").scrollHeight;
    }else{
      b.disabled=true;
      kutu.innerHTML=`<div class="dusunuyor" style="margin-top:16px">
        <span class="yaziyor"><i></i><i></i><i></i></span><span>Düşünüyorum…</span></div>`;
    }
    try{
      const g=Object.assign({soru:soru||"",gecmis:MANEVI_GECMIS.slice(0,-1),
        model:seciliModel()},OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ});
      const r=await fetch("/api/v1/manevi",{method:"POST",
        headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
      const dd=await r.json();
      if(!r.ok)throw new Error(sunucuHatasi(dd,r.status));
      if(soru){
        const w=$("mBekle"); if(w)w.remove();
        MANEVI_GECMIS.push({rol:"danisman",metin:dd.yanit});
        $("mAkis").insertAdjacentHTML("beforeend",
          `<div class="balon ai"><div class="govde">${md(dd.yanit)}</div></div>`);
        $("mAkis").scrollTop=$("mAkis").scrollHeight;
      }else{
        MANEVI_GECMIS=[];
        kutu.innerHTML=`<div class="sentez-metin">${md(dd.yanit)}</div>`;
        $("mnSohbet").style.display="block"; $("mAkis").innerHTML="";
      }
    }catch(e){
      const w=$("mBekle"); if(w)w.remove();
      const m=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
      if(soru)$("mAkis").insertAdjacentHTML("beforeend",`<div class="balon ai"><div class="govde">${m}</div></div>`);
      else kutu.innerHTML=m;
    }finally{ b.disabled=false; }
  };
  b.onclick=()=>cagir("");
  $("mGonder").onclick=()=>cagir($("mSoru").value.trim());
  $("mSoru").addEventListener("keydown",e=>{if(e.key==="Enter")cagir($("mSoru").value.trim());});
}

async function sehirKur(){
  const u=$("sehirUlke"), b=$("sehirBolge"), c=$("sehirSec");
  if(!u)return;
  u.innerHTML=ULKELER.map(x=>`<option value="${esc(x.kod)}">${esc(x.ad)}</option>`).join("");
  u.value="TR";
  const bolgeDoldur=async()=>{
    b.innerHTML='<option>yükleniyor…</option>'; c.innerHTML="";
    let d; try{ d=await ulkeYukle(u.value); }catch(e){ b.innerHTML='<option>alınamadı</option>'; return; }
    const adlar=Object.keys(d.bolgeler).sort((x,y)=>x.localeCompare(y,"tr"));
    b.innerHTML=adlar.map(a=>`<option value="${esc(a)}">${esc(a==="—"?"(bölgesiz)":a)}</option>`).join("");
    sehirDoldur();
  };
  const sehirDoldur=()=>{
    const d=ULKE_ONBELLEK[u.value]; if(!d)return;
    const l=d.bolgeler[b.value]||[];
    c.innerHTML=l.map((x,i)=>`<option value="${i}">${esc(x.ad)}</option>`).join("");
  };
  u.onchange=bolgeDoldur; b.onchange=sehirDoldur;
  await bolgeDoldur();
  $("sehirBtn").onclick=()=>sehirSor("");
  $("sGonder").onclick=()=>sehirSor($("sSoru").value.trim());
  $("sSoru").addEventListener("keydown",e=>{if(e.key==="Enter")sehirSor($("sSoru").value.trim());});
}

async function sehirSor(soru){
  const u=$("sehirUlke"), b=$("sehirBolge"), c=$("sehirSec");
  const d=ULKE_ONBELLEK[u.value]; if(!d)return;
  const x=(d.bolgeler[b.value]||[])[+c.value]; if(!x)return;
  const kutu=$("sehirSonuc"), btn=$("sehirBtn");
  if(soru){
    $("sSoru").value="";
    SEHIR_GECMIS.push({rol:"kullanici",metin:soru});
    $("sAkis").insertAdjacentHTML("beforeend",
      `<div class="balon ben"><div class="govde">${esc(soru)}</div></div>`);
    $("sAkis").insertAdjacentHTML("beforeend",
      `<div class="balon ai" id="sBekle"><div class="govde"><span class="yaziyor"><i></i><i></i><i></i></span></div></div>`);
    $("sAkis").scrollTop=$("sAkis").scrollHeight;
  }else{
    btn.disabled=true;
    kutu.innerHTML=`<div class="dusunuyor" style="margin-top:16px">
      <span class="yaziyor"><i></i><i></i><i></i></span><span>Düşünüyorum…</span></div>`;
  }
  try{
    const g=Object.assign({ad:x.ad,enlem:x.lat,boylam:x.lon,soru:soru||"",
      gecmis:SEHIR_GECMIS.slice(0,-1),rol:ROL,model:seciliModel()},
      OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ});
    const r=await fetch("/api/v1/sehir",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
    const dd=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(dd,r.status));
    if(soru){
      const w=$("sBekle"); if(w)w.remove();
      SEHIR_GECMIS.push({rol:"danisman",metin:dd.yanit});
      $("sAkis").insertAdjacentHTML("beforeend",
        `<div class="balon ai"><div class="govde">${md(dd.yanit)}</div></div>`);
      $("sAkis").scrollTop=$("sAkis").scrollHeight;
    }else{
      SEHIR_SON=dd; SEHIR_GECMIS=[];
      const cz=dd.cozumleme||{}, yk=cz.yakin_cizgiler||[];
      kutu.innerHTML=`<div class="kartlar" style="margin-top:18px">
        ${kart(esc(x.ad),
          (yk.length?yk.slice(0,6).map(l=>kv(l.cisim+" "+l.cizgi,l.uzaklik_km+" km")).join("")
                    :"<p>Belirgin çizgi yok.</p>")+
          ((cz.sessiz_kapasiteler||[]).length
            ? kv("Burada sessiz",cz.sessiz_kapasiteler.map(s=>s.cisim).join(", ")):""),
          cz.okuma, cz.yontem)}
      </div><div class="sentez-metin">${md(dd.yanit)}</div>`;
      $("sehirSohbet").style.display="block";
      $("sAkis").innerHTML="";
    }
  }catch(e){
    const w=$("sBekle"); if(w)w.remove();
    const m=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
    if(soru)$("sAkis").insertAdjacentHTML("beforeend",`<div class="balon ai"><div class="govde">${m}</div></div>`);
    else kutu.innerHTML=m;
  }finally{ btn.disabled=false; }
}

async function izdusumUret(){
  const b=$("izdusumBtn"), kutu=$("izdusumSonuc");
  if(!b)return;
  const eski=b.textContent; b.disabled=true; b.textContent="Yeryüzü taranıyor…";
  kutu.innerHTML=`<div class="dusunuyor" style="margin-top:16px">
    <span class="yaziyor"><i></i><i></i><i></i></span>
    <span>Her noktada harita yeniden kuruluyor…</span></div>`;
  try{
    const r=await fetch("/api/v1/arz-izdusumu",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(girdiTopla())});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    const k=d.en_keskin_esik||{}, y=d.en_yumusak_esik||{};
    kutu.innerHTML=`<div class="kartlar" style="margin-top:18px">
      ${kart("En keskin karar eşiği",
        kv("Konum",k.enlem+"°, "+k.boylam+"°")+kv("Keskinlik",k.asimetri)+
        kv("Ağırlık düşen alan",k.kd_ev+". ev"),
        "Burada kararlar net kutuplaşır — net karar isteyen için kolaylık, esneklik isteyen için baskı.")}
      ${kart("En yumuşak eşik",
        kv("Konum",y.enlem+"°, "+y.boylam+"°")+kv("Keskinlik",y.asimetri)+
        kv("Ağırlık düşen alan",y.kd_ev+". ev"),
        "Burada seçenekler açık kalır; karar ertelenebilir.")}
      ${kart("Tarama",
        kv("Nokta",d.nokta_sayisi)+kv("Yayılım",d.asimetri_yayilimi)+
        kv("Hatalı nokta",d.hatali_nokta),
        d.okuma, d.sinir)}
    </div>`;
  }catch(e){
    kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(e))}</p>`;
  }finally{ b.disabled=false; b.textContent=eski; }
}

function formulKur(){
  const kutu=$("formulKutu"); if(!kutu)return;
  kutu.innerHTML=FORMUL_KATMAN.map(k=>
    `<label class="kutucuk"><input type="checkbox" value="${esc(k.kod)}">
      <span>${esc(k.ad)}</span></label>`).join("");
  const secili=()=>[...kutu.querySelectorAll("input:checked")].map(x=>x.value);
  kutu.addEventListener("change",()=>{
    const n=secili().length;
    const b=$("formulBtn");
    b.textContent = n<2 ? "En az iki katman seçin" :
                    n>6 ? "En fazla altı katman" : `Bağı kur (${n} katman)`;
    b.disabled = n<2 || n>6;
  });
  $("formulBtn").disabled=true;
  $("formulBtn").textContent="En az iki katman seçin";
  $("formulBtn").onclick=async()=>{
    const k=secili(), b=$("formulBtn"), kutu2=$("formulSonuc");
    const eski=b.textContent; b.disabled=true; b.textContent="Bağ kuruluyor…";
    kutu2.innerHTML=`<div class="dusunuyor" style="margin-top:16px">
      <span class="yaziyor"><i></i><i></i><i></i></span>
      <span>Seçilen katmanlar karşılaştırılıyor…</span></div>`;
    try{
      const g=Object.assign({katmanlar:k,rol:ROL,model:seciliModel()},
        OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
      const r=await fetch("/api/v1/formul",{method:"POST",
        headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
      const d=await r.json();
      if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
      FORMUL_METNI=d.formul; FORMUL_GECMIS=[];
      kutu2.innerHTML=`<div class="sentez-metin">${md(d.formul)}</div>
        <button type="button" class="indir" id="fKopya" style="margin-top:14px">Kopyala</button>`;
      $("fKopya").onclick=e=>panoyaKopyala(d.formul,e.target);
      $("formulSohbet").style.display="block";
      $("fAkis").innerHTML="";
    }catch(err){
      kutu2.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">${esc(kullaniciyaHata(err))}</p>`;
    }finally{ b.disabled=false; b.textContent=eski; }
  };
  const sor=async()=>{
    const metin=$("fSoru").value.trim(); if(!metin)return;
    $("fSoru").value="";
    FORMUL_GECMIS.push({rol:"kullanici",metin});
    $("fAkis").insertAdjacentHTML("beforeend",
      `<div class="balon ben"><div class="govde">${esc(metin)}</div></div>`);
    $("fAkis").insertAdjacentHTML("beforeend",
      `<div class="balon ai" id="fBekle"><div class="govde">
        <span class="yaziyor"><i></i><i></i><i></i></span></div></div>`);
    $("fAkis").scrollTop=$("fAkis").scrollHeight;
    try{
      const g=Object.assign({soru:metin,gecmis:FORMUL_GECMIS.slice(0,-1),
        model:seciliModel(),gosterilen:FORMUL_METNI},
        OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD});
      const r=await fetch("/api/v1/chat",{method:"POST",
        headers:{"Content-Type":"application/json"},body:JSON.stringify(g)});
      const d=await r.json();
      if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
      $("fBekle").remove();
      FORMUL_GECMIS.push({rol:"danisman",metin:d.yanit});
      $("fAkis").insertAdjacentHTML("beforeend",
        `<div class="balon ai"><div class="govde">${md(d.yanit)}</div></div>`);
    }catch(err){
      const w=$("fBekle"); if(w)w.remove();
      $("fAkis").insertAdjacentHTML("beforeend",
        `<div class="balon ai"><div class="govde" style="color:var(--kirmizi)">${esc(kullaniciyaHata(err))}</div></div>`);
    }
    $("fAkis").scrollTop=$("fAkis").scrollHeight;
  };
  $("fGonder").onclick=sor;
  $("fSoru").addEventListener("keydown",e=>{if(e.key==="Enter")sor();});
}

function sentezBlogu(no){
  return blok(no,"Bütünsel okuma",`
    <p class="ipucu" style="margin-top:0">Bütün katmanlar tek bir okumada
      birleştirilir; farklı yönler farklı şey söylüyorsa çelişki saklanmaz.</p>
    <button type="button" class="hesapla" id="sentezBtn"
      style="margin-top:14px">Bütünsel okumayı yaz</button>
    <div id="sentezSonuc"></div>`,"sentez");
}

async function panoyaKopyala(metin, dugme){
  try{
    await navigator.clipboard.writeText(metin);
    const e=dugme.textContent; dugme.textContent="Kopyalandı ✓";
    setTimeout(()=>dugme.textContent=e,1600);
  }catch(err){
    // clipboard API HTTPS dışında engellidir; eski yöntemle dene
    const t=document.createElement("textarea");
    t.value=metin; t.style.position="fixed"; t.style.opacity="0";
    document.body.appendChild(t); t.select();
    try{ document.execCommand("copy"); dugme.textContent="Kopyalandı ✓"; }
    catch(e2){ dugme.textContent="Kopyalanamadı"; }
    t.remove(); setTimeout(()=>dugme.textContent="Kopyala",1600);
  }
}

async function sentezUret(){
  const btn=$("sentezBtn"), kutu=$("sentezSonuc");
  if(!btn||!SON_ANALIZ)return;
  const eski=btn.textContent; btn.disabled=true; btn.textContent="Yazılıyor…";
  kutu.innerHTML=`<div class="dusunuyor" style="margin-top:16px">
    <span class="yaziyor"><i></i><i></i><i></i></span>
    <span id="sDusun">Katmanlar birleştiriliyor…</span></div>`;
  try{
    const govde=OTURUM?{oturum:OTURUM,rol:ROL,model:seciliModel()}
                      :{analiz:SON_ANALIZ,mod:SON_MOD,rol:ROL,model:seciliModel()};
    const r=await fetch("/api/v1/sentez",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify(govde)});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    kutu.innerHTML=`<div class="sentez-metin">${md(d.sentez)}</div>
      <button type="button" class="indir" id="sentezKopya" style="margin-top:14px">Kopyala</button>
      <button type="button" class="indir" id="yazdirBtn" style="margin-top:14px">Yazdır / PDF</button>`;
    SENTEZ_METNI=d.sentez;
    $("sentezKopya").onclick=e=>panoyaKopyala(d.sentez,e.target);
    $("yazdirBtn").onclick=yazdir;
    btn.textContent="Yeniden yaz";
  }catch(err){
    kutu.innerHTML=`<p class="ipucu" style="color:var(--kirmizi)">Okuma
      üretilemedi. ${esc(kullaniciyaHata(err))}</p>`;
    btn.textContent=eski;
  }finally{ btn.disabled=false; }
}
let SENTEZ_METNI="";

/* ============ 12 — AI DANIŞMAN ============ */
// Öneri metinleri danışan diliyle: modele terim sorulursa terimle cevap
// verir. Sorular sade tutulunca yanıt da sade geliyor.
const ONERILER=["Hayatımda tekrar eden asıl döngü ne?",
  "Şu an neyin arasında sıkışmış durumdayım?",
  "İş hayatımda neyi değiştirmeliyim?",
  "İlişkilerimde tekrar eden hatam ne?",
  "Önümüzdeki aylarda ne zaman harekete geçmeliyim?",
  "Bu hafta yapabileceğim somut bir şey söyle"];

function sohbetBlogu(no){
  const oneriHtml=ONERILER.map(o=>`<button class="oneri" type="button">${esc(o)}</button>`).join("");
  const govde=`
    <div class="sohbet">
      <div class="sohbet-ust sohbet-model-kilit">
        <span class="et">Danışman modeli</span>
        <strong>${esc(KILITLI_MODEL||((SON_ANALIZ&&SON_ANALIZ.ai||{}).model)||"oturum modeli")}</strong>
        <span class="model-kilit-rozet">🔒 oturuma kilitli</span>
      </div>
      <div class="sohbet-akis" id="akis">
        <div class="balon o">
          <div class="kim"><i style="background:var(--turkuaz)"></i>Danışman</div>
          <div class="govde">Analiz tamamlandı; haritanın tamamı önümde. Ne sormak istersin? Kararsız kaldığın somut bir durumu anlatırsan daha işe yarar bir cevap verebilirim.</div>
        </div>
      </div>
      <div class="oneriler" id="oneriler">${oneriHtml}</div>
      <div class="sohbet-giris">
        <input id="soru" placeholder="Sorunuzu yazın…" autocomplete="off">
        <button id="gonder" type="button">Sor</button>
      </div>
    </div>`;
  return blok(no,"Danışman",govde,"sohbet");
}

/* Hafif markdown → HTML. ÖNCE kaçışlanır, sonra sınırlı etiket açılır:
   ham "#", "**", "---" işaretleri ekranda görünmesin diye. */
function md(t){
  let x=esc(String(t||"").trim());
  // NOT: burada \s KULLANILMAZ — \s yeni satırı da yutar ve blokları birleştirir.
  // Başlık silinmez, işaretlenir: silinseydi "## 1. Eşik" satırı numaralı liste
  // sanılıp <li> olurdu. Başlıklar kendi bloklarına ayrılır.
  x=x.replace(/^[ \t]*#{1,6}[ \t]*(.+?)[ \t]*$/gm,"\n\u0001$1\n");
  x=x.replace(/^[ \t]*(-{3,}|\*{3,}|_{3,})[ \t]*$/gm,"");   // yatay çizgi
  x=x.replace(/\*\*([^*\n]+)\*\*/g,"<strong>$1</strong>");
  x=x.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g,"$1<em>$2</em>");
  x=x.replace(/`([^`\n]+)`/g,"<strong>$1</strong>");
  const parcalar=[];
  x.split(/\n{2,}/).forEach(blok=>{
    const satir=blok.split("\n").map(l=>l.trim()).filter(Boolean);
    let tampon=[];
    const bosalt=()=>{
      if(!tampon.length)return;
      if(tampon.every(l=>/^([-•*]|\d+[.)])[ \t]+/.test(l)))
        parcalar.push("<ul>"+tampon.map(l=>"<li>"+l.replace(/^([-•*]|\d+[.)])[ \t]+/,"")+"</li>").join("")+"</ul>");
      else parcalar.push("<p>"+tampon.join("<br>")+"</p>");
      tampon=[];
    };
    satir.forEach(l=>{
      if(l[0]==="\u0001"){ bosalt(); parcalar.push("<p><strong>"+l.slice(1)+"</strong></p>"); }
      else tampon.push(l);
    });
    bosalt();
  });
  return parcalar.join("") || "<p></p>";
}

function balon(kim,metin,hata){
  const ben=kim==="ben";
  return `<div class="balon ${ben?"ben":"o"}${hata?" hata":""}">
    <div class="kim"><i style="background:${ben?"var(--murekkep)":"var(--turkuaz)"}"></i>${ben?"Sen":"Danışman"}</div>
    <div class="govde">${ben?esc(metin):md(metin)}</div></div>`;
}

/* Modeller gateway'den çekilir; AI_MODEL ortam değişkenine gerek kalmaz. */
let MODELLER=[];
async function modelleriYukle(){
  const sec=$("modelSec"), elle=$("modelElle");
  if(!sec)return;
  try{
    const r=await fetch("/api/v1/ai-models");
    const d=await r.json();
    MODELLER=d.modeller||[];
    sec.innerHTML="";
    if(MODELLER.length){
      MODELLER.forEach(m=>{
        const o=new Option(m.ad+(m.sahip?"  ·  "+m.sahip:"")+(m.erisilemez?"  (plan kapalı)":""),m.id);
        if(m.erisilemez)o.disabled=true;
        sec.add(o);
      });
      const hedef=KILITLI_MODEL||d.varsayilan;
      if(hedef&&MODELLER.some(m=>m.id===hedef))sec.value=hedef;
      elle.style.display="none";
      if(KILITLI_MODEL)modelKilitle(true,KILITLI_MODEL);
    }else{
      sec.add(new Option("liste alınamadı — elle yazın",""));
      elle.style.display="block";
      if(d.varsayilan)elle.value=d.varsayilan;
    }
  }catch(e){
    sec.innerHTML=""; sec.add(new Option("liste alınamadı — elle yazın",""));
    elle.style.display="block";
  }
}
function seciliModel(){
  if(KILITLI_MODEL)return KILITLI_MODEL;
  const s=$("modelSec"), e=$("modelElle");
  const v=(s&&s.value)||"";
  return v || ((e&&e.value.trim())||null);
}
function modelKilitle(kilit,model){
  if(model)KILITLI_MODEL=model;
  const s=$("modelSec"), e=$("modelElle"), b=$("modelKilidiAc"), bilgi=$("modelKilitBilgi");
  if(s)s.disabled=!!kilit; if(e)e.disabled=!!kilit;
  if(b)b.style.display=kilit?"inline-flex":"none";
  if(b&&!b.dataset.kuruldu){ b.dataset.kuruldu="1"; b.onclick=()=>{
    KILITLI_MODEL=null; OTURUM=null; SON_ANALIZ=null;
    $("sonuc").innerHTML=""; $("sonuc").style.display="none";
    modelKilitle(false); modelleriYukle(); yoneticiPanelGuncelle(null);
  };}
  if(bilgi)bilgi.textContent=kilit?`🔒 ${KILITLI_MODEL||"model"} · oturum boyunca sabit`:"Analiz başlamadan seçilir";
}

async function solarReturnBagla(){
  if(!OTURUM||!SON_ANALIZ)return;
  const y=parseInt((document.getElementById("srBaglaYil")||{}).value);
  const btn=document.getElementById("srBaglaBtn");
  if(!y||y<1800||y>2200)return;
  const eski=btn?btn.textContent:"";
  if(btn){btn.disabled=true;btn.textContent="Bağlanıyor…";}
  try{
    const r=await fetch("/api/v1/solar-return-bagla",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({oturum:OTURUM,year:y})});
    const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    Object.assign(SON_ANALIZ,d.degisen||{});
    SON_ANALIZ.solar_v2=d.solar_v2;
    SON_ANALIZ.hukum=d.hukum;
    if(d.referans)SON_ANALIZ.referans=d.referans;
    const srC=$("srAktif"), srY=$("sryil");
    if(srC)srC.checked=true;
    if(srY){srY.disabled=false;srY.value=String(y);}
    sahneAnalizSifirla();
    if(d.oruntu_omurgasi)SON_ANALIZ.oruntu_omurgasi=d.oruntu_omurgasi;
    SON_ANALIZ.kisisel=d.kisisel||SON_ANALIZ.kisisel||{};
    if(d.ai&&d.ai.model){KILITLI_MODEL=d.ai.model;modelKilitle(true,KILITLI_MODEL);}
    ciz(SON_ANALIZ);
    oturumYedekle();
    const hk=document.querySelector('[data-kimlik="hukum"]');
    if(hk)hk.scrollIntoView({behavior:"smooth",block:"start"});
  }catch(e){
    if(btn){btn.disabled=false;btn.textContent=eski||"Solar Return bağla";}
    alert(kullaniciyaHata(e));
  }
}
document.addEventListener("click",e=>{
  const b=e.target&&e.target.closest?e.target.closest("#srBaglaBtn"):null;
  if(b){e.preventDefault();solarReturnBagla();}
});

/* Bekleme metni tek ve sade. Önceden "Berzah'ı tartıyorum", "Çatalı
   açıyorum" gibi ifadeler dönüyordu; bunlar hem teknik terim sızdırıyor
   hem de kullanıcıya hiçbir şey söylemiyordu. */
const DUSUNME=["Düşünüyorum"];

async function soruSor(metin){
  if(!metin||!SON_ANALIZ)return;
  const akis=$("akis"), gonder=$("gonder"), giris=$("soru");
  const oner=$("oneriler"); if(oner)oner.style.display="none";
  akis.insertAdjacentHTML("beforeend",balon("ben",metin));
  akis.insertAdjacentHTML("beforeend",
    `<div class="balon o" id="bekle"><div class="kim"><i style="background:var(--turkuaz)"></i>Danışman</div>
     <div class="govde"><span class="dusunuyor"><span class="yaziyor"><i></i><i></i><i></i></span>
     <span id="dusunMetin">Düşünüyorum…</span> <span class="sure" id="dusunSure">0 sn</span></span></div></div>`);
  akis.scrollTop=akis.scrollHeight;
  giris.value=""; gonder.disabled=true; giris.disabled=true;
  SOHBET.push({rol:"danisan",metin:metin});
  const t0=Date.now(); let adim=0;
  const sayac=setInterval(()=>{
    const sn=Math.round((Date.now()-t0)/1000);
    const ms=$("dusunMetin"), ss=$("dusunSure");
    if(!ms){clearInterval(sayac);return;}
    if(sn>0&&sn%4===0){adim=(adim+1)%DUSUNME.length;}
    ms.textContent=(DUSUNME[adim%DUSUNME.length]||"Düşünüyorum")+"…"; ss.textContent=sn+" sn";
  },1000);
  try{
    const r=await fetch("/api/v1/chat",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(Object.assign(
        {soru:metin,gecmis:SOHBET.slice(0,-1),model:seciliModel(),
         gosterilen:ekrandakiler()},
        OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD}))});
    const d=await r.json();
    clearInterval(sayac);
    $("bekle").remove();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
    akis.insertAdjacentHTML("beforeend",balon("o",d.yanit));
    oturumYedekle(); SOHBET.push({rol:"danisman",metin:d.yanit});
  }catch(err){
    clearInterval(sayac);
    const bek=$("bekle"); if(bek)bek.remove();
    akis.insertAdjacentHTML("beforeend",
      // Hata metni kullanıcıya İÇ BİLGİ SIZDIRMAZ: uç adresleri, sunucu
      // adları ve yığın izleri saldırgana harita çizer. Kullanıcının
      // yapabileceği tek şey tekrar denemektir; söylenecek olan da odur.
      balon("o", kullaniciyaHata(err), true));
  }finally{
    gonder.disabled=false; giris.disabled=false; giris.focus();
    akis.scrollTop=akis.scrollHeight;
  }
}

/* Danışan ekranda zaten bir şeyler okudu; model bunu bilmezse tekrar eder. */
function ekrandakiler(){
  const p=[];
  if(SENTEZ_METNI)p.push(SENTEZ_METNI);
  document.querySelectorAll("#sonuc .mk-govde").forEach(e=>p.push(e.innerText));
  document.querySelectorAll('#sonuc [data-kis]').forEach(e=>p.push(e.textContent));
  return p.join("\n").slice(0,5000);
}

function sohbetKur(){
  SOHBET=[];
  const g=$("gonder"), i=$("soru");
  if(!g)return;
  g.onclick=()=>soruSor(i.value.trim());
  i.onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();soruSor(i.value.trim());}};
  document.querySelectorAll("#oneriler .oneri").forEach(btn=>
    btn.onclick=()=>soruSor(btn.textContent));
}

/* ============ OTOMATİK KİŞİSELLEŞTİRME ============ */
/* Hüküm satırları herkes için birebir aynıydı; Çatal cümleleri 12 satırlık
   burç tablosundan geliyordu. Altı harita ölçüldüğünde sayılar 6/6 benzersiz
   çıkarken metin 3/6 kalıyordu. Bu katman hesabı DEĞİŞTİRMEZ, yalnız metni
   haritaya özgü hâle getirir; başarısız olursa şablon metin yerinde kalır. */
/* Kişiselleştirme artık SUNUCUDA, analizle aynı istekte tamamlanır.
   v3.1'de arayüz önce şablon metni basıp sonra ayrı bir çağrı yapıyordu;
   çağrı düşünce ekranda kırmızı ham hata kutusu kalıyordu. O kutu kaldırıldı:
   yorum gelirse satırlar dolu gelir, gelmezse şablon metin sessizce durur. */
function kisiselUygula(d){
  const alanlar=(d && d.kisisel) || {};
  let n=0;
  Object.entries(alanlar).forEach(([k,v])=>{
    if(!v)return;
    document.querySelectorAll(`[data-kis="${k}"]`).forEach(el=>{el.textContent=v;n++;});
  });
  return n;
}

/* ============ ana çizici ============ */
let SON_ANALIZ=null, SON_MOD="Kişisel", SOHBET=[];

function cizIliski(d){
  let H="", no=2;   // v2.8'de kompozitte 3 numarası atlanıyordu; sıra artık kesintisiz
  if(d.sinastri){
    const sn=d.sinastri;
    H+=blok(no++,`Sinastri · ${sn.kisiler.A} ↔ ${sn.kisiler.B}`,`
      ${kv("Denge",sn.denge.okuma)}
      ${kv("Destek / sınav",sn.denge.destek+" / "+sn.denge.sinav)}
      ${kv("Majör açı",sn.denge.major_aci)}
      <div class="kartlar" style="margin-top:24px">
        ${kart("Önemli temaslar",sn.onemli_temaslar.map(t=>
          kv(t.a+" "+t.glif+" "+t.b,t.orb+"°")).join(""),
          sn.onemli_temaslar.map(t=>t.baslik+": "+t.anlam).join(" · "))}
        ${kart("Tüm çapraz açılar",sn.capraz_acilar.slice(0,10).map(t=>
          kv(t.a+" "+t.glif+" "+t.b,t.aci+" "+t.orb+"°")).join(""))}
        ${Object.entries(sn.ev_bindirmesi).map(([k,v])=>kart(k.replace(/_/g," "),
          v.filter(x=>x.yogun_ev).concat(v.slice(0,5)).slice(0,6)
           .map(x=>kv(x.gezegen,x.ev+". ev")).join(""),
          (v.find(x=>x.yogun_ev)||{}).anlam||null)).join("")}
      </div>`,"sinastri");
    const ab=sn.alan_bukmesi;
    H+=blok(no++,"Alan bükmesi · BERZAH'a özgü ölçü",`<div class="kartlar">${
      Object.entries(ab).filter(([k,v])=>typeof v==="object"&&v.yorum)
       .map(([k,v])=>kart(k.replace(/_/g," "),
         kv("KD yalnız",v.KD_yalniz)+kv("KD birlikte",v.KD_birlikte)+
         kv("KD kayması",v.KD_kaymasi+"°")+
         (v.Berzah_kaymasi!=null?kv("Berzah kayması",v.Berzah_kaymasi+"°"):""),
         v.yorum)).join("")}</div>
      <p class="ipucu">${esc(ab.yontem)}</p>`,"alanbukmesi");
  }
  if(d.kompozit){
    const k=d.kompozit, kb2=k.berzah_v2, b2=kb2.berzah;
    H+=blok(no++,`Kompozit · ${k.kisiler.A} & ${k.kisiler.B}`,`
      ${kv("Kompozit ASC",k.harita.ASC)}${kv("Kompozit MC",k.harita.MC)}
      ${kv("Ev sistemi",k.harita.ev_sistemi)}
      ${kv("İlişkinin Kara Deliği",kb2.KD.konum+" · "+kb2.KD.ev+". ev")}
      ${kv("İlişkinin Ak Deliği",kb2.AD.konum)}
      ${b2?kv("İlişkinin Berzahı",b2.konum+" · "+b2.tur):""}
      ${b2?`<p class="soru" style="margin-top:26px">“<span data-kis="catal_soru">${esc(b2.catalin_cumlesi)}</span>”</p>
        <div class="cift">
          <div class="yanlis"><div class="ust"><i></i>Yanlış refleks</div><span data-kis="catal_yanlis">${esc(b2.yanlis_refleks)}</span></div>
          <div class="dogru"><div class="ust"><i></i>Berzah hamlesi</div><span data-kis="catal_dogru">${esc(b2.berzah_hamlesi)}</span></div>
        </div>`:""}
      <p class="ipucu">${esc(k.okuma)}</p>
      <div class="kartlar" style="margin-top:24px">
        ${kart("Kompozit gezegenler",k.harita.gezegenler.map(g=>
          kv(g.cisim,g.konum+" · "+g.ev+". ev")).join(""),null,k.uyari)}
      </div>`,"kompozit");
  }
  const dv=d.davison||{};
  if(dv && !dv.hata && dv.harita){
    const db=(dv.berzah_v2||{}).berzah||{};
    H+=blok(no++,"Davison · ilişkinin zaman haritası",`
      ${kv("Orta an",dv.an||"—")}${kv("ASC",dv.harita.ASC||"—")}${kv("MC",dv.harita.MC||"—")}
      ${db.konum?kv("Davison Berzahı",db.konum+(db.tur?" · "+db.tur:"")):""}
      <div class="kartlar" style="margin-top:18px">${kart("Gerçek orta nokta",
        kv("Enlem",(dv.konum||{}).enlem)+kv("Boylam",(dv.konum||{}).boylam)+
        kv("Aritmetik ortalamadan sapma",((dv.konum||{}).aritmetik_ortalamadan_sapma_km||0)+" km"),
        dv.okuma||"",dv.yontem||"")}</div>`,"davison");
  }
  const dk=d.deklinasyon||{};
  if(dk && !dk.hata){
    const giz=(dk.gizli_baglar||[]);
    H+=blok(no++,"Deklinasyon · görünmeyen bağlar",`
      ${kv("Gizli bağ",dk.gizli_sayi!=null?dk.gizli_sayi:giz.length)}
      <div class="kartlar" style="margin-top:18px">${giz.length?giz.slice(0,8).map(x=>kart(
        `${x.a} ↔ ${x.b}`,kv("Tür",x.tur)+kv("Orb",x.orb+"°"),null,"Klasik boylam açısında görünmeyen temas.")).join(""):
        kart("Gizli deklinasyon bağı yok","Bu haritada klasik sinastrinin dışında ek paralel/karşıt-paralel görünmedi.")}</div>
      <p class="ipucu">${esc(dk.okuma||"")}</p>`,"deklinasyon");
  }
  const asr=d.A_solar_v2||null, bsr=d.B_solar_v2||null;
  if((asr&&!asr.hata)||(bsr&&!bsr.hata)){
    const srKart=(x,ad)=>{const vv=(x||{}).berzah_v2||{}, bb=vv.berzah||{};return kart(`${ad} · SR ${x.yil||""}`,
      kv("KD",(vv.KD||{}).konum||"—")+kv("AD",(vv.AD||{}).konum||"—")+kv("Berzah",bb.konum||"—"),
      null,"Bu yıllık katman kişinin natal yapısının yerine geçmez; ilişkiye taşıdığı yıllık aktivasyonu gösterir.");};
    H+=blok(no++,"Solar Return · ilişkiye taşınan yıllık aktivasyon",`<div class="kartlar">
      ${asr&&!asr.hata?srKart(asr,(d.girdi.A||{}).ad||"A"):""}
      ${bsr&&!bsr.hata?srKart(bsr,(d.girdi.B||{}).ad||"B"):""}
    </div>`,"iliski_solar");
  }

  ["A_berzah","B_berzah"].forEach((anahtar,i)=>{
    const v=d[anahtar]; if(!v)return;
    const ad=(d.girdi[anahtar[0]]||{}).ad||anahtar[0];
    const bb=v.berzah;
    H+=blok(no++,`${ad} · kendi alanı`,`
      ${kv("Kara Delik",v.KD.konum+" · "+v.KD.ev+". ev")}
      ${kv("Ak Delik",v.AD.konum)}
      ${bb?kv("Berzah",bb.konum+" · "+bb.tur):""}
      ${bb?kv("Çatalın cümlesi",bb.catalin_cumlesi):""}
      ${bb?kv("Berzah hamlesi",bb.berzah_hamlesi):""}`, i===0?"kisi_a":"kisi_b");
  });
  ILISKI_NO=no;
  return H;
}
let ILISKI_NO=6;

function ciz(d){
  HALKA_SETI=halkaSeti(d); HALKA_SECIM=0; HUDUD=d.hudud_felek||null;
  TRANSIT=(d.transit&&!d.transit.hata)?d.transit:null; CIFT="kapali";

  /* MİSAFİR KİPİ — yalnız harita ve danışman.
     Sunucu zaten hesaplanan modüllerin ham verisini göndermiyor; burada
     arayüz de yalnız bu iki bölümü çizer. */
  if(ROL==="misafir"){
    const v2m=(HALKA_SETI[0]||{}).v2||{};
    const bz=v2m.berzah||{};
    const ad=(d.girdi||{}).ad||"";
    const kat=d.kategoriler||{};
    let M=`<div class="misafir-bas">
      <div class="mb-et">Okumanız hazır</div>
      <h2 class="mb-ad">${esc(ad||"Doğum haritanız")}</h2>
      <p class="mb-alt">Aşağıda sizin hakkınızda çıkan okumalar var. Her
        başlığın altındaki düğmeyle o konuyu derinleştirebilir, en altta
        danışmana dilediğinizi sorabilirsiniz.</p>
    </div>`;

    if(kat._hata){
      M+=`<p class="ipucu" style="color:var(--kirmizi)">Okumalar şu an
        üretilemedi. Danışman bölümünden yine de soru sorabilirsiniz.</p>`;
    }
    // Kategori kartları — teknik terim yok, yalnız kişiye dair yorum.
    let no=1;
    MIS_KAT.forEach(k=>{
      const metin=kat[k.kod];
      if(!metin)return;
      M+=blok(no++, k.ad, `
        <div class="mk-govde">${md(metin)}</div>
        <button type="button" class="derin" data-bolum="${esc(MIS_BOLUM[k.kod]||"hukum")}"
          data-baslik="${esc(k.ad)}">Bu konuyu derinleştir</button>`);
    });

    if(HALKA_SETI.length){
      M+=blok(no++,"Haritanız",`<div class="halka-kap">${halka(HALKA_SETI[0].v2)}</div>`);
    }
    M+=sentezBlogu(no++);
    M+=sohbetBlogu(no);
    $("sonuc").innerHTML=M;
    sohbetKur(); halkaBagla(); gezinmeKur(); katlamaKur(); derinBaslik();
  icindekilerKur(); aramaKur(); sunumKur(); girisCubuguKur(); yukariKur(); oturumYedekle();
    if($("sentezBtn"))$("sentezBtn").onclick=sentezUret;
    document.querySelectorAll("#sonuc .derin").forEach(b=>
      b.onclick=()=>bolumAnalizi(b.dataset.bolum,b.dataset.baslik));
    return;
  }

  /* İLİŞKİ MODU — sinastri ve kompozitin kendi çizicisi.
     NOT: bu dal v4.1'de misafir görünümü yazılırken yanlışlıkla silinmişti;
     sinastri ve kompozit kişisel çiziciye düşüp `d.berzah_v2` bulamadığı için
     sessizce patlıyordu (hata gizli #durum kutusuna yazılıyordu). */
  if(d.sinastri||d.kompozit){
    const govdeH=cizIliski(d);
    let ekH="";
    if(HALKA_SETI.length){
      ekH=blok(ILISKI_NO++,"Alan halkası · Φ(λ)",
        `<div class="halka-kap">${halka(HALKA_SETI[0].v2)}</div>`,"halka");
    }
    $("sonuc").innerHTML=govdeH+ekH+sentezBlogu(ILISKI_NO++)+sohbetBlogu(ILISKI_NO);
    sohbetKur(); aiDugmeleriBagla(); halkaBagla();
    if($("sentezBtn"))$("sentezBtn").onclick=sentezUret;
    gezinmeKur(); kategoriMerkeziKur(d); katlamaKur(); derinBaslik(); icindekilerKur(); aramaKur();
  sunumKur(); girisCubuguKur(); yukariKur(); yoneticiPanelGuncelle(d); oturumYedekle(); kisiselUygula(d);
    sahneKur(d);
    return;
  }

  const v2=d.berzah_v2, kb=d.kabzbast_v1_m66_74, dn=d.deneme_modulleri,
        kd_=d.kadim_katman, hd=d.human_design, b=v2.berzah;
  const kurt=v2.kurtarici&&v2.kurtarici[0];
  let H="";

  /* Rektifikasyon sonucu — Hüküm'ün hemen üstünde, çünkü tüm ev katmanının
     ne kadar güvenilir olduğunu bu belirler. */
  const rk=d.rektifikasyon;
  if(rk && rk.durum){
    const enp=Math.max(...(rk.egri||[{puan:1}]).map(x=>x.puan))||1;
    const cubuk=(rk.egri||[]).map(x=>
      `<i class="${x.puan>=enp?"en":""}" style="height:${Math.max(4,x.puan/enp*100).toFixed(0)}%" title="${esc(x.saat)} · ${x.puan}"></i>`).join("");
    H+=`<div class="rekt ${esc(rk.durum)}">
      <div class="rekt-bas">Doğum saati · ${rk.durum==="kesin"?"olaylardan çözüldü"
        :rk.durum==="zayif"?"eğilim var, teyit gerekir":"çözülemedi — saat değiştirilmedi"}</div>
      <div class="rekt-saat">${rk.onerilen_saat
        ?`<s>${esc(rk.verilen_saat)} →</s>${esc(rk.onerilen_saat)}`
        :esc(rk.verilen_saat)}</div>
      <div class="rekt-egri">${cubuk}</div>
      ${kv("Keskinlik",rk.keskinlik)}${kv("Rastgeleye üstünlük (p)",rk.p_degeri)}
      ${kv("Açıklanan olay",(rk.kapsanan_olay!=null?rk.kapsanan_olay:"—")+" / "+rk.olay_sayisi)}
      <p class="ipucu">${esc((rk.karar||{}).kesin||"")}</p>
      ${(rk.en_iyi_temaslar||[]).length?`<div class="usul">${
        rk.en_iyi_temaslar.map(t=>esc(t.tarih)+" · "+esc(t.temas||"—")).join("<br>")}</div>`:""}
    </div>`;
  }

  H+=mizan5Blogu(d);

  const hukumV=d.hukum||{};
  const hSolar=(hukumV.solar||null);
  const hTetik=((hukumV.cross||{}).tetiklenmeler||[]).slice(0,4);
  const hMeta=hSolar
    ? `<div class="hukum-baglam"><div><strong>Natal + ${esc(hSolar.yil||"Solar Return")}</strong><span>Solar Return yıllık aktivasyon olarak Hüküm'e dahil edildi.</span></div>
       ${hTetik.length?`<div class="hukum-tetik">${hTetik.map(t=>`<span>${esc(t.solar)} → ${esc(t.natal)} · ${esc(t.aci)} · orb ${esc(t.orb)}°</span>`).join("")}</div>`:""}</div>`
    : `<div class="hukum-baglam solar-bagla"><div><strong>Yıllık aktivasyon bağlı değil</strong><span>Natal Hüküm korunur; istersen Solar Return ekleyip yalnız Hüküm katmanını yeniden hesaplayabilirsin.</span></div>
       ${OTURUM?`<div class="solar-bagla-form"><input id="srBaglaYil" type="number" min="1800" max="2200" value="${new Date().getFullYear()}"><button id="srBaglaBtn" type="button" class="indir">Solar Return bağla</button></div>`:""}</div>`;

  const hukumBlok=blok(2,"Hüküm",`
    ${hMeta}
    <div class="hsatir"><span class="n">01</span>
      <span class="rol"><i style="background:var(--sari)"></i>Şikâyet</span>
      <span class="icerik">Ak Delik <span class="vurgu">${esc(v2.AD.konum)}</span>${v2.AD.ev?` · ${v2.AD.ev}. ev`:""} — <span data-kis="sikayet">danışanın getirdiği cümle buradan çıkar.</span></span></div>
    <div class="hsatir"><span class="n">02</span>
      <span class="rol"><i style="background:var(--murekkep)"></i>Sebep</span>
      <span class="icerik">Kara Delik <span class="vurgu">${esc(v2.KD.konum)}</span>${v2.KD.ev?` · ${v2.KD.ev}. ev`:""} — <span data-kis="sebep">söylemediği şey burada.</span></span></div>
    ${b?`<div class="hsatir"><span class="n">03</span>
      <span class="rol"><i style="background:var(--kirmizi)"></i>Karar</span>
      <span class="icerik">Berzah <span class="vurgu">${esc(b.konum)}</span>${b.ev?` · ${b.ev}. ev`:""} — <span data-kis="karar">${esc(b.tur)}, asimetri ${esc(b.asimetri)}×</span></span></div>`:""}
    <div class="hsatir"><span class="n">04</span>
      <span class="rol"><i style="background:var(--turkuaz)"></i>Talimat</span>
      <span class="icerik">${kurt
        ?`<span class="vurgu">${esc(kurt.gezegen)}</span> Kara Delik'e ${esc(kurt.aci)}°, altın açıdan ${esc(kurt.sapma)}° sapma — <span data-kis="talimat">${esc(kurt.durum)}.</span>`
        :`<span data-kis="talimat">Altın açı adayı hesaplanamadı.</span>`}</span></div>`,"hukum");

  const halkaBlok=blok(3,"Alan halkası · Φ(λ)",`<div class="halka-kap">${halka(v2)}</div>`,"halka");
  H+=`<div class="ana-dashboard">${halkaBlok}${hukumBlok}</div>`;
  H+=kategoriSinyalBloklari(d);

  if(b){
    H+=blok(4,`Çatal · ${b.iki_deniz.a} ↔ ${b.iki_deniz.b}`,`
      <p class="soru">“<span data-kis="catal_soru">${esc(b.catalin_cumlesi)}</span>”</p>
      ${kv("Çatalın adı",b.catalin_adi)}
      ${kv("Kapsam",b.kapsam)}
      ${kv("Saf iki-deniz eşiği",b.saf_esik)}
      ${kv("Alan sapması",b.alan_sapmasi+"°")}
      ${kv("En yakın gezegen",b.en_yakin_gezegen+"°")}
      ${kv("Denge",b.denge_tipi||"—")}
      ${b.sahne?`<div class="kv"><span>Sahne</span><b data-kis="catal_sahne">${esc(b.sahne)}</b></div>`:""}
      ${b.tetikleyici?kv("Tetikleyici",b.tetikleyici):""}
      <div class="cift">
        <div class="yanlis"><div class="ust"><i></i>Yanlış refleks</div><span data-kis="catal_yanlis">${esc(b.yanlis_refleks)}</span></div>
        <div class="dogru"><div class="ust"><i></i>Berzah hamlesi</div><span data-kis="catal_dogru">${esc(b.berzah_hamlesi)}</span></div>
      </div>
      ${b.guven?`<div class="duzeltici">${esc(b.guven)}</div>`:""}
      ${(b.duzelticiler||[]).map(x=>`<div class="duzeltici">${esc(x)}</div>`).join("")}`,"catal");
  }

  const enb=Math.max(...v2.kutleler.map(m=>Math.abs(m.m)));
  H+=blok(5,"Kütleler",
    v2.kutleler.map(m=>`<div class="kutle"><span>${GLIF[m.gezegen]||""} ${esc(m.gezegen)}</span>
      <span class="cubuk-yol"><span class="cubuk ${m.m<0?"eksi":""}" style="width:${(Math.abs(m.m)/enb*100).toFixed(0)}%"></span></span>
      <span class="deger">${m.m>0?"+":""}${m.m.toFixed(2)}</span></div>`).join("")+
    `<div class="usul">Asalet × hız × açısallık (gerçek mundan konum) × görünürlük × deklinasyon. Retrograd işareti çevirir: itici kütle.</div>`,"kutleler");

  let ek="";
  if(v2.mercekleme.length)ek+=kart("Mercekleme",
    v2.mercekleme.slice(0,4).map(l=>kv(l.gezegen+(l.cift_goruntu?" ★":""),l.gercek+" → "+l.gorunen)).join(""),
    v2.mercekleme.some(l=>l.cift_goruntu)?"★ Einstein halkası: bu tema hayatta iki ayrı yerde belirir ve kişi ikisini aynı şey olarak görmez.":null);
  if(v2.yapisal_ikizler.length)ek+=kart("Yapısal ikizler",
    v2.yapisal_ikizler.slice(0,4).map(t=>kv(t.a+" ↔ "+t.b,"kapı "+t.kapi_a+"/"+t.kapi_b+" · H"+t.hamming)).join(""),
    "Açı yokken bile bir çizgi farkıyla bağlı çiftler.");
  const anlamli=v2.oz_modul_spektrumu.filter(s=>s.fdr);
  ek+=kart("Öz-modül spektrumu",
    (anlamli.length?anlamli:v2.oz_modul_spektrumu.slice(0,3))
      .map(s=>kv("M = "+s.M+"°","R "+s.R+" · p "+s.p+(s.fdr?" ✓":""))).join(""),
    anlamli.length?"FDR'den geçen modüller. Uranyen 90° bu listede yoksa kişinin dial'ı 90 değildir."
                  :"Hiçbir zirve FDR eşiğini geçmedi — bu haritada baskın öz-modül yok.");
  if(v2.asal_acilar.length)ek+=kart("Asal açılar",
    v2.asal_acilar.slice(0,4).map(a=>kv(a.a+" — "+a.b,a.kat+"×(360/"+a.asal+") = "+a.aci+"°")).join(""),
    "İndirgenemez açılar: hiçbir alt harmoniğe bölünmez.");
  ek+=kart("Kurtarıcı adayları",
    (v2.kurtarici||[]).map(k=>kv(k.gezegen,k.aci+"° · sapma "+k.sapma+"°")).join(""),
    "Altın açı 137.508°: tekrar etmeyen tek bölüm — döngüden çıkış kanalı.");
  H+=blok(6,"Alanın kenarları",`<div class="kartlar">${ek}</div>`,"kenarlar");

  /* ---- v3.0: alan topolojisi ---- */
  const at=v2.alan_topolojisi||{};
  if(at && !at.hata){
    const hv=at.havza||{}, ey=at.esik_yuksekligi||{}, hi=at.himmet||{}, kl=at.kalicilik||{};
    let T="";
    T+=kart("Havza tayini · nerede yaşıyorsun",
      (hv.gostergeler||[]).map(g=>kv(g.gosterge+" "+g.konum,g.havza)).join("")+
      kv("Baskın havza",hv.yasanan_havza||"—"),hv.yorum,hv.yontem);
    if(!ey.hata)T+=kart("Eşik yüksekliği · himmet",
      kv("Su bölümü",ey.su_bolumu)+kv("Berzah'tan sapma",ey.berzahtan_sapma+"°")+
      kv(ey.sol.havza+" tarafı",ey.sol.bariyer+"  (or. "+ey.sol.oransal+")")+
      kv(ey.sag.havza+" tarafı",ey.sag.bariyer+"  (or. "+ey.sag.oransal+")")+
      kv("Çıkışı kolay yön",ey.kolay_yon),
      "Bir havzadan ötekine geçmek Φ bakımından inilmesi gereken miktardır — "+
      "aktivasyon enerjisinin karşılığı. İki taraf farklıysa bir yönden çıkmak diğerinden zordur.");
    if(hi && !hi.hata)T+=kart("Dayanıklılık ve geçirgenlik",
      kv("Dayanıklılık",hi.dayaniklilik+" · "+hi.dilim)+
      kv("Ortalama bariyer",hi.ortalama_bariyer)+
      kv("En düşük",hi.en_dusuk.ay+" · "+hi.en_dusuk.bariyer)+
      (hi.gecirgenlik_pencereleri||[]).slice(0,4).map(x=>
        kv("Pencere "+x.ay,"bariyer "+x.bariyer)).join(""),
      hi.band,hi.yontem);
    if(kl.ozellikler)T+=kart("Kalıcılık · hangi tepe gerçek",
      (kl.ozellikler||[]).slice(0,6).map(o=>
        kv(o.konum,(o.oransal!=null?o.oransal:"∞")+" · "+o.sinif)).join("")+
      kv("Yapısal özellik",kl.yapisal_sayi+" / "+kl.tepe_sayisi),
      null,kl.yontem);
    H+=blok(7,"Alan topolojisi · havza, eşik, kalıcılık",
      `<div class="kartlar">${T}</div>`,"topoloji");
  }

  /* ---- DURAKLAMA İZİ (yalnız yönetici) ----
     Chrono-Gravitron'un yerine geldi. O modül gravitasyonu hesaplıyordu
     ama sistem yerçekiminin nedensel rolü olmadığını zaten söylüyordu —
     dürüstlüğünü kanıtlamak için var olan bir katmandı, seansta
     kullanılamıyordu. Bu modül doğrudan kullanılabilir bir şey söyler. */
    H+=blok(8,"Duraklama izi · işlenmiş ve ham yanlar",`
    <p class="ipucu" style="margin-top:0">Gezegenler yılda birkaç kez
      <b>durur</b> — o an gökyüzünde hareketsizdirler ve bir natal noktanın
      üzerindeyse temasın en yoğun hâlidir. Doğumdan bugüne hangi yanlar
      <b>defalarca işlenmiş</b>, hangileri <b>hiç dokunulmamış</b>.</p>
    ${(function(){
      const D=d.duraklama_izi||{};
      if(!D||D.hata) return '<p class="ipucu">Hesaplanamadı.</p>';
      const ham=(D.el_degmemis||[]).map(x=>x.nokta);
      return `<div class="dr-ozet">
        <div><span class="et">Yaş</span><b>${D.yas}</b></div>
        <div><span class="et">Temas</span><b>${D.temas_eden}</b>
          <i>${D.toplam_duraklama} duraklamadan</i></div>
        <div><span class="et">Ham kalan</span><b>${ham.length}</b>
          <i>${ham.length?esc(ham.join(", ")):"yok"}</i></div>
      </div>
      <div class="dr-liste"><span class="et">İşlenmiş yanlar</span>
        ${(D.islenmis||[]).map(r=>{
          const son=(r.kayitlar||[]).slice(-1)[0]||{};
          const g=Math.min(100,Math.round(r.sayi/Math.max(1,(D.islenmis[0]||{}).sayi||1)*100));
          return `<div class="dr-satir">
            <span class="dr-ad">${esc(r.nokta)}</span>
            <span class="dr-bar"><i style="width:${g}%"></i></span>
            <span class="dr-say">${r.sayi}×</span>
            <span class="dr-son">${son.tarih?esc(son.tarih)+" "+esc(son.cisim||""):"—"}</span>
          </div>`;}).join("")}
      </div>
      ${ham.length?`<div class="dr-ham"><span class="et">Hiç dokunulmamış</span>
        <p>${esc(ham.join(", "))} — kapasite var, sınanmamış. Bu yanlarda
        kişi toydur; tavsiye verirken bunu hesaba katın.</p></div>`:""}
      ${(D.ilk_kez_yaklasan||[]).length?`<div class="dr-ilk">
        <span class="et">İlk kez işlenecek</span>
        ${D.ilk_kez_yaklasan.map(y=>`<p><b>${esc(y.tarih)}</b> ${esc(y.cisim)}
          → ${esc(y.nokta)} üzerinde duruyor</p>`).join("")}</div>`:""}
      <p class="ipucu">${esc(D.sinir||"")}</p>`;
    })()}`,"duraklama");

  /* ---- v3.9: Hudûd-ı Felek — deklinasyon ve küresel alan ---- */
  const hf=d.hudud_felek||{};
  if(hf && !hf.hata){
    const pa=hf.paralel||{}, hd=hf.hudud_disi||{}, ka=hf.kuresel_alan||{};
    const kk=ka.kuresel_KD||{}, kb=ka.kuresel_berzah||{};
    let HH="";
    HH+=kart("Gizli bağlar · deklinasyon",
      (pa.gizli_baglar||[]).slice(0,6).map(x=>
        kv(x.a+" "+(x.tur==="paralel"?"∥":"⊼")+" "+x.b, x.orb+"° · "+x.dekl_a+" / "+x.dekl_b)).join("")
      || "<p>Gizli bağ yok.</p>", pa.okuma, pa.yontem);
    HH+=kart("Tüm deklinasyon temasları",
      (pa.temaslar||[]).slice(0,8).map(x=>
        kv(x.a+" "+(x.tur==="paralel"?"∥":"⊼")+" "+x.b,
           x.orb+"°"+(x.boylam_acisi?" · "+x.boylam_acisi:" · gizli"))).join("")
      || "<p>Temas yok.</p>",
      "∥ paralel: aynı yönde çalışırlar. ⊼ karşıt-paralel: birbirini dengeler.");
    HH+=kart("Hudûd dışı",
      kv("Eğiklik",hd.egiklik+"°")+
      ((hd.hudud_disi||[]).map(x=>kv(x.cisim,x.dekl+"° · "+x.asim+"° aşım ("+x.yon+")")).join(""))+
      ((hd.sinirdakiler||[]).map(x=>kv(x.cisim+" (sınırda)",x.dekl+"° · "+x.asim+"°")).join("")),
      hd.okuma, hd.yontem);
    HH+=kart("Küresel alan · Φ(α,δ)",
      kv("Küresel Kara Delik",(kk.ekliptik_boylam||"—")+(kk.ev?" · "+kk.ev+". ev":""))+
      kv("Boylam Kara Deliği",(ka.boylam_KD||{}).konum||"—")+
      kv("Sapma",(ka.sapma_derece!=null?ka.sapma_derece:"—")+"°")+
      kv("En yakın cisim",(kk.en_yakin_cisim||"—")+" ("+(kk.en_yakin_ayrim||"—")+"°)")+
      (kb.ekliptik_boylam?kv("Küresel eşik",kb.ekliptik_boylam+" · "+kb.iki_deniz):""),
      ka.yorum, ka.yontem);
    H+=blok(9,"Hudûd-ı Felek · deklinasyon ve küresel alan",
      `<div class="kartlar">${HH}</div>
       <p class="ipucu">${esc(hf.uyari||"")}</p>`,"hudud");
  }

  /* ---- v3.1: Şi'râ çevrimi ---- */
  const sc=d.sira_cevrimi||{};
  if(sc && !sc.hata){
    const sa=sc.sira_a||{}, sb=sc.sira_b||{}, on=sc.oneriler||{};
    const ALAN=[["fikir","Fikir"],["dusunce","Düşünce"],["duygu","Duygu"],["plan","Plan"],
                ["aliskanliklar","Alışkanlıklar"],["kararlilik","Kararlılık"],
                ["yasam_tarzi","Yaşam tarzı"],["degisim","Değişim"]];
    const d0=sb.dogumda||{}, n0=sb.bugun||{};
    // yörünge şeridi: ayrıklık 0.41 → 1.59 aralığında iki imleç
    const kon=v=>((v-0.409)/(1.591-0.409)*100).toFixed(1);
    H+=blok(10,"Şi'râ Çevrimi · Tarık nefesi",`
      <p class="ipucu" style="margin-top:0">${esc(sc.aciklama)}</p>
      <div class="sira-serit">
        <div class="sira-yol">
          <span class="sira-im dogum" style="left:${kon(d0.ayriklik)}%" title="doğum"></span>
          <span class="sira-im simdi" style="left:${kon(n0.ayriklik)}%" title="bugün"></span>
        </div>
        <div class="terazi-etiket"><span>Perigeon · en yakın</span><span>Apogeon · en uzak</span></div>
      </div>
      <div class="kartlar" style="margin-top:22px">
        ${kart("Şi'râ A · görünen",kv("Doğumda",(sa.dogumda||{}).konum)+
          kv("Bugün",(sa.bugun||{}).konum)+kv("Presesyon kayması",sa.presesyon_kaymasi+"°")+
          kv("Menzil",(sc.menzil||{}).no+" · "+(sc.menzil||{}).ad),
          (sc.temaslar||[]).length?"Natal temas: "+sc.temaslar.map(t=>t.cisim+" "+t.tur+" ("+t.orb+"°)").join(", "):"Natal cisimlerle dar orbda temas yok.")}
        ${kart("Şi'râ B · görünmeyen",
          kv("Doğum fazı",d0.faz+" · "+d0.ceyrek)+kv("Doğum ayrıklığı",d0.ayriklik)+
          kv("Bugünkü faz",n0.faz+" · "+n0.ceyrek)+kv("Bugünkü ayrıklık",n0.ayriklik)+
          kv("Yön",n0.yaklasiyor?"yaklaşıyor — kapanma":"uzaklaşıyor — açılma")+
          kv("Sonraki perigeon",n0.sonraki_perigeon),
          "P = "+(sb.yorunge||{}).P_yil+" yıl · e = "+(sb.yorunge||{}).e+" · "+(sb.yorunge||{}).kaynak)}
        ${kart("Tarık dönüşü",kv("Tam dönüş",(sc.tarik_donusu||{}).tam_donus_yillari.join(" · "))+
          kv("Yarı dönüş",(sc.tarik_donusu||{}).yari_donus),(sc.tarik_donusu||{}).not)}
        ${sc.yildizname?kart("Osmanlı yıldıznâmesi",
          kv("Ebced",sc.yildizname.ebced)+kv("Yıldız burcu",sc.yildizname.burc)+
          kv("Tabiat",sc.yildizname.tabiat),sc.yildizname.aciklama,sc.yildizname.yontem):""}
      </div>
      <div class="sira-oneri">
        ${ALAN.filter(([k])=>on[k]).map(([k,ad])=>`
          <div class="oneri-kutu">
            <div class="oneri-bas"><span>${esc(ad)}</span><i>${esc(on[k].olcum)}</i></div>
            <p class="oneri-durum">${esc(on[k].durum)}</p>
            <p class="oneri-eylem">${esc(on[k].oneri)}</p>
          </div>`).join("")}
      </div>
      <p class="ipucu">${esc(sc.uyari)}</p>`,"sira");
  }

  /* Yürüyen Berzah bölümü v12.3'te silindi ama `konum`, `eks` ve `net`
     değişkenleri ORADA tanımlanıyordu ve Kabz/Bast onları kullanıyor.
     Sonuç: ciz() "konum is not defined" ile çöküyor ve HİÇBİR bölüm
     çizilmiyordu — v12.4 bu hâliyle paketlendi.
     Üçü de Kabz/Bast'ın kendi verisinden yeniden türetildi. */
  const eks = (kb && kb.eksen) || {};
  const net = (typeof eks.net === "number" ? eks.net
               : (typeof kb?.net === "number" ? kb.net : 0));
  const konum = Math.max(0, Math.min(100,
    50 + (typeof net === "number" ? net : 0) * 5));

  H+=blok(12,"Kabz / Bast · modül 66–74",`
    <div class="terazi"><span class="dolgu" style="left:50%;width:${Math.abs(konum-50).toFixed(1)}%;${konum<50?'transform:translateX(-100%)':''}"></span><span class="ibre" style="left:calc(${konum.toFixed(1)}% - 1.5px)"></span></div>
    <div class="terazi-etiket"><span>Kabz</span><span>Eşik</span><span>Bast</span></div>
    <p style="margin:16px 0 0;font-size:15.5px">${esc(eks.kutup)} — Σκ·m = ${esc(net)}</p>
    <div class="kartlar" style="margin-top:26px">
      ${kb.m68_einstein_rosen.length?kart("Birincil köprü (m68)",
        kb.m68_einstein_rosen.slice(0,3).map(x=>kv(x.kabz+" → "+x.bast,"güç "+x.guc)).join(""),
        kb.m68_einstein_rosen[0].cumle):""}
      ${kart("Kuramoto & LQC (m70·m72)",
        kv("Faz uyumu C",kb.m70_kuramoto.C)+kv("ρ/ρc",kb.m72_lqc.rho_orani)+
        kv("Durum",kb.m72_lqc.durum)+kv("Anlık sıçrama",kb.m73_anlik_sicrama))}
      ${kart("528 Hz imza (m71)",
        kv("Kök ton",kb.m71_528hz.kok_ton)+kv("Frekans",kb.m71_528hz.kok_hz+" Hz")+
        kv("Pürüzlülük",kb.m71_528hz.puruzluluk))}
      ${kb.m69_ufuk_bogaz.length?kart("Ufuk / boğaz (m69)",
        kb.m69_ufuk_bogaz.slice(0,4).map(x=>kv(x.cisim,x.isaret.join(", "))).join("")):""}
      ${kb.solar_return?kart("Solar Return "+kb.solar_return.yil,
        kv("Δ eğrilik",kb.solar_return.delta_egrilik)+kv("Yön",kb.solar_return.yon)+
        kv("Köprü yılı",kb.solar_return.kopru_yili?"EVET":"hayır")):""}
      ${kb.m74_gecit.pencereler.length?kart("Tayy-i Mekân (m74)",
        kb.m74_gecit.pencereler.slice(0,5).map(w=>kv(w.tarih,"geçit "+w.gecit_skoru)).join(""),
        null,"Geçit skoru = 0.45·sıçrama + 0.30·C + 0.25·(ρ/ρc)"):""}
    </div>`,"kabzbast");

  const D=[];
  D.push(kart("Kader Rezonans Noktası",kv("KRN",dn.krn.KRN.konum)+kv("Ev",say(dn.krn.KRN.ev))+
    kv("Anti-KRN",dn.krn.Anti_KRN.konum)+kv("Skor",dn.krn.skor+" · "+dn.krn.seviye),null,dn.krn.yontem));
  D.push(kart("Vahdet Noktası",kv("Nokta",dn.vahdet.vahdet_noktasi?dn.vahdet.vahdet_noktasi.konum:"—")+
    kv("R indeksi",dn.vahdet.R_indeksi)+kv("Baskın harmonik","H"+dn.vahdet.baskin_harmonik.H),dn.vahdet.rejim));
  D.push(kart("Mizan Alanı",
    (dn.mizan.sekineler.slice(0,3).map(s=>kv("Sekîne",s.konum)).join(""))+
    (dn.mizan.berzahlar.slice(0,2).map(s=>kv("Berzah",s.konum)).join("")),
    "Tepeler makam, çukurlar eşiktir."));
  D.push(kart("Asabiyye Matrisi",
    kv("Bağlılık dilimi","%"+dn.asabiyye.yuzdelik)+kv("λ₂ (Fiedler)",dn.asabiyye.ic_baglilik_lambda2)+
    kv("Bağ sayısı",dn.asabiyye.kenar_sayisi+" / 45")+kv("Blok",dn.asabiyye.ada_sayisi)+
    kv("Reis",dn.asabiyye.reis)+kv("Menteşe",dn.asabiyye.mentese)+
    (dn.asabiyye.yalnizlar&&dn.asabiyye.yalnizlar.length?kv("Yalnız",dn.asabiyye.yalnizlar.join(", ")):"")+
    (dn.asabiyye.en_guclu_baglar||[]).slice(0,3).map(e=>kv(e.a+" – "+e.b,e.aci+" "+e.orb+"°")).join(""),
    dn.asabiyye.yorum+" · Fay hattı: "+(dn.asabiyye.fay_hatti.kamp_A||[]).join(", ")+" ↔ "+(dn.asabiyye.fay_hatti.kamp_B||[]).join(", ")));
  D.push(kart("Arş Ekseni",kv("Eğim",dn.ars_ekseni.egim_derece+"°")+
    kv("Çıkıntı",dn.ars_ekseni.cikinti.cisim),dn.ars_ekseni.yon));
  D.push(kart("Felek Saati",dn.felek_saati.en_yavas_saatler.slice(0,4)
    .map(c=>kv(c.cift,c.periyot_yil+" yıl"+(c.kavusum_efemeris?" · "+c.kavusum_efemeris:""))).join(""),
    dn.felek_saati.rezonant_kilitler.length?"Rezonant kilit: "+dn.felek_saati.rezonant_kilitler[0].oran:null));
  D.push(kart("Ayna Ekseni",kv("Eksen",dn.ayna_ekseni.eksen.konum)+
    kv("Simetri",dn.ayna_ekseni.simetri_skoru)+kv("Gizli ikiz",dn.ayna_ekseni.gizli_ikizler.length),
    dn.ayna_ekseni.gizli_ikizler.length?dn.ayna_ekseni.gizli_ikizler.map(t=>t.a+"↔"+t.b).join(", "):null));
  D.push(kart("Devr-i Daim",(dn.devri_daim.tecdid_pencereleri||[]).slice(0,4)
    .map(t=>kv(t.tarih,"%"+t.benzerlik)).join(""),"Desenin gökte yeniden kurulduğu yıllar."));
  D.push(kart("Nokta-i Süveyda",kv("Süveyda",dn.suveyda.suveyda.konum)+
    kv("Kalp–küll farkı",dn.suveyda.kalp_kull_farki+"°")+kv("Çeken aykırı",dn.suveyda.ceken_aykiri),
    dn.suveyda.yorum));
  D.push(kart("Mizâc Pusulası",kv("Baskın hılt",dn.mizac_pusulasi.baskin_hilt)+
    Object.entries(dn.mizac_pusulasi.bunye_m0).map(([k,v])=>kv(k,v)).join(""),
    dn.mizac_pusulasi.bakim_aylari.length?"Bakım ayları: "+dn.mizac_pusulasi.bakim_aylari.slice(0,4).join(", "):null));
  D.push(kart("Vuslat Kapıları",(dn.vuslat_kapilari.vuslat_kapilari||[]).slice(0,4)
    .map(g=>kv(g.tarih,g.faz+" · "+g.puan)).join("")||"<p>Ufukta kapı yok.</p>"));
  D.push(kart("İkbal Merdiveni",kv("Zirve",dn.ikbal_merdiveni.zirve.ay+" · "+dn.ikbal_merdiveni.zirve.irtifa)+
    kv("Konsolidasyon",dn.ikbal_merdiveni.konsolidasyon.ay)+
    (dn.ikbal_merdiveni.muhur_tarihleri||[]).slice(0,3).map(m=>kv(m.tarih,m.muhur)).join("")));
  D.push(kart("Sahib-Kırân",(dn.sahib_kiran.pencereler||[]).slice(0,4)
    .map(w=>kv(w.ay,w.tip.replace("Kırân-ı ",""))).join("")||"<p>Kesişen pencere yok.</p>",
    "Kavuşan gezegenler değil, kavuşan takvimler."));
  D.push(kart("Nokta-i İcâbet",kv("İcâbet",dn.nokta_i_icabet.icabet.konum)+
    kv("Ev",say(dn.nokta_i_icabet.icabet.ev))+kv("İbtilâ",dn.nokta_i_icabet.ibtila.konum),
    dn.nokta_i_icabet.icabet.anlam));
  D.push(kart("Nokta-i Noksan",kv("Noksan",dn.nokta_i_noksan.noksan.konum)+
    kv("Unsur",dn.nokta_i_noksan.noksan.unsur)+kv("Derinlik",dn.nokta_i_noksan.noksan.derinlik+" · "+dn.nokta_i_noksan.noksan.derinlik_ad),
    dn.nokta_i_noksan.anlam));
  D.push(kart("Sevk-i Felek v2",kv("Merkez",dn.sevk_i_felek_v2.merkez.konum)+
    kv("dR/dt",dn.sevk_i_felek_v2.kabz_bast_ekseni.dR_dt)+
    kv("Dümenci",dn.sevk_i_felek_v2.dumenci)+kv("Lenger",dn.sevk_i_felek_v2.lenger),
    dn.sevk_i_felek_v2.faz_portresi));
  H+=blok(13,"Deneme modülleri · 16 teknik",`<div class="kartlar">${D.join("")}</div>`,"deneme");

  const lab=kd_.kadim_lab, hv=kd_.huviyet_muhru, it=kd_.isim_tecellisi;
  let K=kart("Hüviyet Mührü",kv("Bütünlük",hv.butunluk_endeksi)+kv("Gerilim",hv.gerilim_endeksi)+
    kv("Kimlik",hv.muhur_kimligi.split(" ")[0]),hv.muhur_kimligi);
  K+=kart("Hyleg & hudûd",kv("Hyleg adayı",lab.hyleg.aday)+kv("Konum",lab.hyleg.konum)+
    kv("Ev",lab.hyleg.ev),lab.etik_ilke);
  K+=kart("Kırân-ı Ekber",kv("Sıradaki kavuşum",lab.kiran_i_ekber.siradaki_kavusum||"—")+
    kv("Konum",lab.kiran_i_ekber.siradaki_kavusum_konum||"—")+
    kv("Unsur devri",lab.kiran_i_ekber.unsur_devri||"—")+
    kv("Şahsî ev",say(lab.kiran_i_ekber.sahsi_ev)),lab.kiran_i_ekber.not);
  if(lab.tasyir&&lab.tasyir.length)K+=kart("Tasyîr",lab.tasyir.slice(0,5)
    .map(t=>kv(t.yonlendirilen+" → "+t.vaad_edici,t.yil+" · "+t.yas+" yaş")).join(""),
    "Sembolik 1°/yıl yönlendirme.");
  if(lab.ihtiyarat_30gun&&lab.ihtiyarat_30gun.length)K+=kart("İhtiyârât · 30 gün",
    lab.ihtiyarat_30gun.slice(0,5).map(i=>kv(i.tarih,i.kalite.split(" ")[0])).join(""));
  if(it)K+=kart("İsim Tecellîsi",kv("Ebced",it.ebced.ebced)+kv("İsim derecesi",it.isim_derecesi.konum)+
    kv("Ev",say(it.isim_derecesi.ev))+kv("Vahdet hizası",it.vahdet_hizasi_derece+"°"),it.mizan_konumu);
  H+=blok(14,"Kadim katman",`<div class="kartlar">${K}</div>`,"kadim");

  H+=blok(15,"Human Design",`<div class="kartlar">
      ${kart(hd.tip.tr,kv("Strateji",hd.strateji)+kv("Profil",hd.profil)+kv("Tanım",hd.tanim)+
        kv("Kanal sayısı",hd.kanallar.length),hd.otorite.tr)}
      ${kart("Merkezler",kv("Tanımlı",hd.tanimli_merkezler.join(", ")||"—")+
        kv("Açık",hd.acik_merkezler.join(", ")||"—"),
        hd.kanallar.length?"Kanallar: "+hd.kanallar.join(" · "):null)}
      ${kart("Not-self tuzakları",hd.not_self_tuzaklari.map(t=>kv(t.tuzak,"")).join(""),
        hd.not_self_tuzaklari.map(t=>t.aciklama).join(" "))}
    </div>`,"hd");

  H+=blok(16,"Ham veri",
    kv("An",d.girdi.an)+kv("UTC ofseti",(d.girdi.tz>=0?"+":"")+d.girdi.tz)+
    kv("Saat dilimi kaynağı",d.girdi.tz_kaynak)+kv("Ev sistemi",d.girdi.ev_sistemi)+
    `<button class="indir" id="indirBtn">JSON indir</button>`,"hamveri");

  /* ---- ASTROKARTOGRAFİ ve ARZ İZDÜŞÜMÜ ---- */
  const kt=d.kartografi||{};
  if(kt && !kt.hata){
    const gd=kt.gunes_donusu||{}, ad_=kt.ay_donusu||{};
    const cizgi=(ak,ad)=>{
      if(!ak||ak.hata)return kart(ad,"<p>Hesaplanamadı.</p>");
      return kart(ad,(ak.cizgiler||[]).slice(0,10).map(c=>
        kv(c.cisim, "MC "+c.MC.toFixed(1)+"°  ·  IC "+c.IC.toFixed(1)+"°"+
           (c.kutup_kesintisi?"  · kutupta kesintili":""))).join(""),
        null, ak.yontem);
    };
    let K="";
    K+=cizgi(kt.natal,"Doğum anı · dikey çizgiler");
    K+=cizgi(gd,"Güneş dönüşü"+(kt.gunes_donusu_an?" · "+kt.gunes_donusu_an:""));
    K+=cizgi(ad_,"Ay dönüşü"+(kt.ay_donusu_an?" · "+kt.ay_donusu_an:""));
    const pr=kt.natal_paran||[];
    K+=kart("Enlem kesişimleri (paran)",
      pr.length?pr.slice(0,8).map(x=>kv(x.a+" × "+x.b,
        (x.enlem!==null&&x.enlem!==undefined?"enlem "+x.enlem+"°":"boylam "+x.boylam+"°")
        +"  · orb "+x.orb)).join(""):"<p>Yakın kesişim yok.</p>",
      "Paran boylamdan bağımsızdır: o enlemin tamamında geçerlidir.");
    // HUDÛD-I ARZ — iki katmanın birleşimi
    const ha=kt.hudud_arz||{};
    if(ha && !ha.hata){
      const ke=ha.kritik_enlem||{}, sk=ha.sessiz_kusaklar||{}, pc=ha.paralel_cizgiler||{};
      K+=kart("Kapının kapandığı enlem",
        (ke.cisimler||[]).slice(0,6).map(x=>
          kv(x.cisim+(x.hudud_disi?" ⚑":""),
             "±"+x.kritik_enlem+"° ötesinde çizgi yok · yüzeyin %"+
             (x.cizgisiz_yuzey_orani*100).toFixed(1)+"'i")).join(""),
        ke.okuma, ke.yontem);
      if((sk.kusaklar||[]).length)
        K+=kart("Sessiz kuşaklar",
          sk.kusaklar.map(x=>kv(x.cisim,
            "±"+x.kuzey_bandi[0]+"° ötesi")).join(""),
          sk.kusaklar[0].anlam);
      if((pc.ciftler||[]).length)
        K+=kart("Birlikte hareket eden çizgiler",
          pc.ciftler.slice(0,5).map(x=>kv(x.a+" ∥ "+x.b,
            x.tur+" · orb "+x.orb)).join(""),
          pc.okuma);
    }
    H+=blok(25,"Yer · astrokartografi",`
      <div class="kartlar">${K}</div>
      <p class="ipucu">${esc((ha||{}).bag||"")}</p>
      <div class="sehir-arac">
        <span class="et">Yer sorgusu</span>
        <select id="sehirUlke"></select>
        <select id="sehirBolge"></select>
        <select id="sehirSec"></select>
        <button type="button" class="ccark" id="sehirBtn">Bu yeri sor</button>
      </div>
      <div id="sehirSonuc"></div>
      <div class="formul-sohbet" id="sehirSohbet" style="display:none">
        <div class="akis" id="sAkis"></div>
        <div class="giris-satir">
          <input id="sSoru" placeholder="Bu yer hakkında sorun…" autocomplete="off">
          <button type="button" class="gonder" id="sGonder">Sor</button>
        </div>
      </div>
      <p class="ipucu">${esc((kt.natal||{}).not_in_mundo||"")}</p>
      <button type="button" class="hesapla" id="izdusumBtn" style="margin-top:16px">Eşiğin yeryüzü izdüşümünü hesapla</button>
      <div id="izdusumSonuc"></div>
      <p class="ipucu">${esc(kt.uyari||"")}</p>`,"kartografi");
  }

  /* ---- SPİRİTÜEL ÇALIŞMALAR ---- */
  const mn=d.maneviyat||{};
  if(mn && !mn.hata && mn.mizan){
    const mz=mz0(mn.mizan), y=mz.yakinsama||{}, vf=mn.vefk||{}, av=mn.amel_vakti;
    let M="";
    M+=kart("Altı geleneğin kapısı",
      (mz.kapilar||[]).map(k=>kv(k.gelenek,k.kapi+(k.sefira?" · "+k.sefira:""))).join(""),
      mz.hukum, mz.kapsam);
    const kb=(mz.kapilar||[]).find(k=>k.eksik_kanal);
    if(kb)M+=kart("Çalışılmamış yer",
      kv("Kanal",kb.eksik_kanal.cisim+" · "+kb.eksik_kanal.sefira)+
      kv("Anlamı",kb.eksik_kanal.anlam),
      "Zayıf olduğunuz yer değil; henüz çalışılmamış olan yer.");
    M+=kart("Örtüşme",
      kv("Yakınsayan kapı",y.kapi||"—")+
      kv("Kaç gelenek",(y.kac_gelenek||0)+" / "+(y.toplam||6))+
      kv("Oran",y.oran),
      mz.hukum, mz.uyari);
    if(av)M+=kart("Çalışma vakti",
      kv("Sahibi",av.sahip)+kv("Başlangıç",av.baslangic)+kv("Bitiş",av.bitis)+
      kv("Tür",av.tur),
      "Gündüz ve gece on ikişer eşit olmayan saate bölünür; bu, yakınsayan kapının bugünkü saati.",
      (mn.gezegen_saatleri||{}).yontem);
    if(vf.kare)M+=kart("Vefk · "+vf.mertebe+"×"+vf.mertebe,
      `<div class="vefk">${vf.kare.map(r=>
        `<div class="vefk-satir">${r.map(x=>`<span>${x}</span>`).join("")}</div>`).join("")}</div>`+
      kv("Sabit toplam",vf.sabit_toplam)+
      kv("Doğrulama",vf.dogrulama&&vf.dogrulama.gecerli?"satır, sütun ve köşegen toplamları tutuyor":"TUTMUYOR"),
      vf.not);
    H+=blok(24,"Spiritüel çalışmalar · kapıların tartısı",`
      <div class="kartlar">${M}</div>
      <p class="ipucu">${esc(mn.cerceve||"")}</p>
      <p class="ipucu">${esc(mn.tesla_notu||"")}</p>
      <button type="button" class="hesapla" id="mnBtn" style="margin-top:16px">Çalışmayı yaz</button>
      <div id="mnSonuc"></div>
      <div class="formul-sohbet" id="mnSohbet" style="display:none">
        <div class="akis" id="mAkis"></div>
        <div class="giris-satir">
          <input id="mSoru" placeholder="Bu çalışma üzerine sorun…" autocomplete="off">
          <button type="button" class="gonder" id="mGonder">Sor</button>
        </div>
      </div>`,"manevi");
  }
  function mz0(x){ return x||{}; }

  /* ---- LUNASYON TAKVİMİ ----
     Astrolog lunasyon takvimi olmadan çalışamaz: her yeni ay bir konu
     açar, her dolunay olgunlaştırır, tutulmalar aylara yayılan kapılar
     açar. Sistem şimdiye kadar yalnız "bugünkü gök" veriyordu. */
  H+=blok(17,"Lunasyon takvimi · ay hafta hafta",`
    <p class="ipucu" style="margin-top:0">Önümüzdeki bir yılın yeni ayları,
      dolunayları ve tutulmaları — haritanızda hangi alana düştüğü ve hangi
      noktalara değdiğiyle. <b>Ağırlık</b>, o olayın sizin için ne kadar
      belirleyici olduğunu gösterir. Satıra dokununca o olayın okuması
      çıkar.</p>
    <button type="button" class="hesapla" id="lunBtn">Takvimi çıkar</button>
    <div id="lunSonuc"></div>`,"lunasyon");

  /* ---- DÖNÜŞ NOKTASI ----
     Astroloji "transit geçti" der; "bu bir daha olmayacak" demez. */
  H+=blok(19,"Dönüş noktası · bir daha gelmeyecek kapılar",`
    <p class="ipucu" style="margin-top:0">Yavaş gezegenler bir noktaya
      ömürde bir ya da iki kez gelir. Plüton bir turu 248 yılda tamamlar —
      bazı kapılar <b>yalnız bir kez</b> açılır. Bu bölüm hangi kapının
      tekrar etmeyeceğini gösterir; zamanlama değil <b>ağırlık</b> bilgisi.</p>
    <button type="button" class="hesapla" id="dnBtn">Kapıları çıkar</button>
    <div id="dnSonuc"></div>`,"donus");

  /* ---- ALGI EŞİĞİ ----
     Astrolojinin tamamı orb üzerine kurulu ama kimse hesaplamıyor.
     Bu bölüm haritanın kendi orbunu türetir. */
  H+=blok(18,"Algı eşiği · fark edilir olmak için ne gerekir",`
    <p class="ipucu" style="margin-top:0">Yoğun bir alanda küçük bir dokunuş
      kaybolur; seyrek bir alanda aynı dokunuş her şeyi değiştirir. Bu bölüm
      <b>bu haritanın kendi orbunu</b> hesaplar — 3° varsayımı yerine.
      Astroloji, transit hissetmeyen kişiyi "farkındalığı düşük" diye
      suçlar; burada onun yerine bir ölçü var.</p>
    <button type="button" class="hesapla" id="esBtn">Eşiği hesapla</button>
    <div id="esSonuc"></div>`,"esik");

  /* ---- SÜKÛT HARİTASI ----
     Astrolojinin tamamı neyin AKTİF olduğu üzerine kurulu. Bu bölüm neyin
     OLMADIĞINI ölçer — ve bir yanlışlama aracı sunar. */
  H+=blok(20,"Sükût haritası · gökyüzünün sustuğu aralıklar",`
    <p class="ipucu" style="margin-top:0">Bir yılın <b>basınç eğrisi</b>:
      gökyüzü haritanıza ne kadar değiyor. Sessiz aralıklarda dışarıdan bir
      itiş yok. <b>Asıl kullanımı:</b> bir dönemden şikâyet ediliyorsa ve o
      dönem sessizse, sebep gökyüzü değildir — başka yere bakmak gerekir.</p>
    <button type="button" class="hesapla" id="skBtn">Eğriyi çıkar</button>
    <div id="skSonuc"></div>`,"sukut");

  /* ---- ÇELİŞKİLER ----
     Katmanlar birbiriyle anlaşamadığında asıl bilgi oradadır. Uydurma
     tutarlılık göstermek yerine çelişkiyi açıkça koyar. */
  const cel=d.celiskiler||[];
  if(cel.length){
    H+=blok(21,"Çelişkiler · sistem kendi içinde ne diyor",`
      <p class="ipucu" style="margin-top:0">Katmanların birbirini
        <b>tutmadığı</b> yerler. Bunlar hata değil — seansta en işe yarayan
        bilgi çoğu zaman burada.</p>
      <div class="kartlar">${cel.map(c=>kart(esc(c.baslik),
        `<div class="celiski-yan"><span class="et">bir yan</span><p>${esc(c.bir_yan)}</p></div>
         <div class="celiski-yan"><span class="et">öbür yan</span><p>${esc(c.obur_yan)}</p></div>`,
        c.ne_yapmali)).join("")}</div>`,"celiski");
  }

  /* ---- DİRENÇ HARİTASI ----
     Danışmanın seansta en çok işine yarayan bilgi: bu kişi neye itiraz
     edecek ve aynı şey nasıl söylenirse dinlenir. */
  const dr=d.direnc||[];
  if(dr.length){
    H+=blok(22,"Direnç · nasıl söylersen dinlenir",`
      <p class="ipucu" style="margin-top:0">Aynı bulgunun kapatan ve açan
        söyleniş biçimi. Sıra ve dil, içerikten çok şeyi belirler.</p>
      <div class="kartlar">${dr.map(x=>kart(esc(x.ne_zaman),
        `<div class="direnc-yan kapatir"><span class="et">kapatır</span><p>${esc(x.kapatir)}</p></div>
         <div class="direnc-yan acar"><span class="et">açar</span><p>${esc(x.acar)}</p></div>`
        )).join("")}</div>`,"direnc");
  }

  /* ---- DANIŞAN SORULARI ----
     Genel okuma yerine belirli sorulara cevap. Her soru hangi katmandan
     cevaplanacağına bağlı olduğu için AI uyduramıyor. */
  H+=blok(23,"Danışan soruları · seçip sor",`
    <p class="ipucu" style="margin-top:0">Kategoriden soru seçin (en fazla 4 — fazlası tek turda yetişmez).
      Her sorunun cevabı kendi katmanından üretilir. Kendi sorunuzu da
      ekleyebilirsiniz.</p>
    <div class="soru-sekme" id="soruSekme"></div>
    <div class="kutucuklar" id="soruListe"></div>
    <label style="display:block;margin-top:18px"><span class="etiket">Kendi sorunuz (isteğe bağlı)</span>
      <input id="soruEk" placeholder="Katalogda olmayan bir şey sormak isterseniz…"></label>
    <button type="button" class="hesapla" id="soruBtn" style="margin-top:16px">Soruları cevapla</button>
    <div class="hazir-sorular" id="hazirKutu" style="display:none">
      <span class="et">Bu harita için hazırlananlar</span>
      <div class="hazir-liste" id="hazirListe"></div>
    </div>
    <div id="soruSonuc"></div>
    <div class="rapor-kut">
      <div>
        <b>Tam rapor</b>
        <p class="ipucu" style="margin:4px 0 0"><b>Danışan raporu</b>: sessiz
          okunmak için, elde kalacak belge. <b>Anlatım metni</b>: seansta
          sesli okumanız için — kısa cümleler, nerede duracağınız, ne
          soracağınız ve arkadaki dayanak. <i>Anlatım metni danışana
          verilmez.</i></p>
      </div>
      <div class="rapor-dugmeler">
        <button type="button" class="hesapla" id="raporBtn" data-tur="danisan">Danışan raporu</button>
        <button type="button" class="ccark" id="raporBtn2" data-tur="anlatim">Anlatım metni</button>
      </div>
    </div>
    <div id="raporDurum"></div>
    <div id="raporMetin"></div>
    <div class="rapor-pdf-kut" id="raporPdfKut" style="display:none">
      <span class="ipucu" style="margin:0">Beğendiğinizde PDF alın.</span>
      <button type="button" class="hesapla" id="raporPdfBtn">PDF indir</button>
    </div>`,"sorular");

  /* ---- FORMÜLASYON ----
     Sentez hepsini birden okur; Formülasyon kullanıcının SEÇTİĞİ katmanlar
     arasında bağ kurar. "Şu üçü birbirine ne diyor" sorusu, seansta
     gerçekten sorulan sorudur. */
  H+=blok(26,"Formülasyon · katmanlar arası bağ",`
    <p class="ipucu" style="margin-top:0">İki ilâ altı katman seçin; yalnız
      onlar arasında bağ kurulur. Katmanlar çelişiyorsa çelişki saklanmaz —
      asıl değerli durum odur.</p>
    <div class="kutucuklar" id="formulKutu"></div>
    <button type="button" class="hesapla" id="formulBtn" style="margin-top:18px">Bağı kur</button>
    <div id="formulSonuc"></div>
    <div class="formul-sohbet" id="formulSohbet" style="display:none">
      <div class="akis" id="fAkis"></div>
      <div class="giris-satir">
        <input id="fSoru" placeholder="Bu bağ üzerine soru sorun…" autocomplete="off">
        <button type="button" class="gonder" id="fGonder">Sor</button>
      </div>
    </div>`,"formul");

  H+=sentezBlogu(27);
  H+=sohbetBlogu(28);
  $("sonuc").innerHTML=H;
  sohbetKur(); aiDugmeleriBagla(); halkaBagla();
  if($("sentezBtn"))$("sentezBtn").onclick=sentezUret;
  formulKur(); maneviKur(); soruKur(); raporKur(); lunasyonKur(); sukutKur(); esikKur(); donusKur(); seansDugmesi(); sunumKur(); misafirSadelestir();
  setTimeout(()=>{ try{ hazirlaSorular(); }catch(e){} }, 1500);
  if($("izdusumBtn"))$("izdusumBtn").onclick=izdusumUret;
  sehirKur();
  if($("dinBtn"))$("dinBtn").onclick=dinamikTara;
  gezinmeKur(); katlamaKur(); derinBaslik(); icindekilerKur(); aramaKur();
  sunumKur(); girisCubuguKur(); yukariKur(); oturumYedekle(); kisiselUygula(d);
  sahneKur(d);
  document.getElementById("indirBtn").onclick=()=>{
    const a=document.createElement("a");
    a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:"application/json"}));
    a.download="berzah-"+(d.girdi.ad||"harita").replace(/\s+/g,"-").toLowerCase()+".json";
    a.click();URL.revokeObjectURL(a.href);
  };
}
  temaKur();
// Model seçimi doğum verisi adımında hazır olmalı.
try{ modelleriYukle(); }catch(e){}
// Yarım kalmış oturum varsa devam teklif edilir.
try{ oturumTeklif(); }catch(e){}

temaKur();

/* ========================================================================
   v13.4 · KALICI KANIT SAHNESİ
   ------------------------------------------------------------------------
   v12.x uzun bir modül listesini daha iyi filtrelemeye çalışıyordu. Asıl
   sorun liste değil, ölçüm ile danışan anlatısının aynı yüzeyde yarışmasıydı.
   Bu katman dört konuşma sahnesi kurar; eski bütün teknik kartlar silinmez,
   Rasathane'ye çekilir. Sahne düzeni /api/v2/harita sözleşmesinden gelir.
   ======================================================================== */
let SAHNE_HARITA=null, SAHNE_ACILIS=null, SAHNE_AKTIF="hukum";
let SAHNE_SONUCLAR={}, SAHNE_ZAMAN=null, SAHNE_YUKLENIYOR=false;
function sahneAnalizSifirla(){
  // Referans yılı yalnız Zaman'ı değil Hüküm, Soru, Belge ve Rasathane
  // kanıtlarını da değiştirir. v13.4.1 yalnız şeridi temizlediği için eski yılın
  // cümleleri yeni SR rozetinin altında kalabiliyordu.
  SAHNE_ZAMAN=null; SAHNE_SONUCLAR={}; SAHNE_ACILIS=null; SAHNE_HARITA=null; GECMIS_OKUMALAR=null;
  try{LUN_TAKVIM=null;SK_HARITA=null;}catch(_e){}
}

function referansEtiketi(){
  const r=(SON_ANALIZ&&SON_ANALIZ.referans)||{};
  return r.kaynak==="solar_return"&&r.yil?`SR ${r.yil}`:"Yalnız Natal";
}
function referansRozeti(){return `<span class="referans-rozet">${esc(referansEtiketi())}</span>`;}
function referansDogum(){
  const gi=girdiTopla();
  const r=(SON_ANALIZ&&SON_ANALIZ.referans)||{};
  if(r.kaynak==="solar_return"&&r.yil)gi.sr_year=+r.yil; else delete gi.sr_year;
  return gi;
}

function sahnePayload(ek={}){
  const temel=OTURUM?{oturum:OTURUM}:{analiz:SON_ANALIZ,mod:SON_MOD,model:seciliModel()};
  return Object.assign(temel,ek);
}
async function v2Post(yol,ek={}){
  const r=await fetch(yol,{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify(sahnePayload(ek))});
  const d=await r.json();
  if(!r.ok)throw new Error(sunucuHatasi(d,r.status));
  return d;
}
function sahneKanitHtml(kanit){
  return (kanit||[]).map(k=>`<button type="button" class="sahit-rozet ${k.durum==="var"?"var":"sessiz"}"
    data-kanit="${esc(k.kod)}" title="${k.durum==="var"?"Bu katmanda veri var":"Bu katman bu analizde sessiz"}">
    <i></i>${esc(k.kod.replaceAll("_"," "))}</button>`).join("");
}
function sahneMetaHtml(x){
  if(!x)return "";
  const k=x.kapsam||{}, dar=Math.round((+k.daralma||0)*100), t=x.tekrar_detay||{};
  const isn=(x.isnad_orani==null)?null:Math.round((+x.isnad_orani||0)*100);
  const hasv=(x.hasv_orani==null)?null:Math.round((+x.hasv_orani||0)*100);
  return `<div class="sahne-metin-meta">
    <span>tekrar <b>%${Math.round((+x.tekrar||0)*100)}</b></span>
    ${(t.sozel!=null||t.iddia!=null)?`<span>sözel/iddia <b>%${Math.round((+t.sozel||0)*100)} / %${Math.round((+t.iddia||0)*100)}</b></span>`:""}
    ${k.tam_bayt!=null?`<span>bağlam <b>-%${dar}</b></span>`:""}
    ${isn!=null?`<span class="${isn<50?"uyari":""}">isnâd <b>%${isn}</b></span>`:""}
    ${hasv!=null?`<span class="${hasv>0?"uyari":""}">haşv <b>%${hasv}</b></span>`:""}
    ${x.yeniden_yazildi?`<span class="uyari">tekrar nedeniyle yeniden yazıldı</span>`:""}
    ${(x.sizinti||[]).length?`<span class="uyari">teknik sızıntı: ${esc(x.sizinti.join(", "))}</span>`:`<span>teknik sızıntı <b>0</b></span>`}
  </div>`;
}
function iddiaGeriHtml(x){
  const ls=x&&x.iddialar||[]; if(!ls.length)return "";
  return `<details class="iddia-geri"><summary>İddia defteri · ${ls.length} doğrulanabilir kayıt</summary><div>${ls.map(i=>`<article><span>${esc(i.davranis||"genel")} · ${esc(i.alan)} · ${esc(i.yon)} · ${esc(i.zaman)}</span><nav><button type="button" data-iddia-id="${esc(i.id)}" data-iddia-sonuc="tuttu">tuttu</button><button type="button" data-iddia-id="${esc(i.id)}" data-iddia-sonuc="tutmadı">tutmadı</button><button type="button" data-iddia-id="${esc(i.id)}" data-iddia-sonuc="belirsiz">belirsiz</button></nav></article>`).join("")}</div></details>`;
}
function sahneMetinHtml(x){
  if(!x)return "";
  const ps=x.paragraflar||[];
  if(!ps.length)return `<div class="sahne-metin">${md(x.metin||"")}</div>`;
  return `<div class="isnad-metin">${ps.map(p=>`<div class="isnad-paragraf${p.hasv?" hasv-paragraf":""}"><div class="sahne-metin">${md(p.metin||"")}</div><div class="isnad-yan">${p.hasv?`<span class="isnad-rozet hasv">haşv</span>`:""}${p.dayanaksiz?`<span class="isnad-rozet dayanaksiz">dayanaksız</span>`:(p.dayanak||[]).map(k=>`<button type="button" class="isnad-rozet" data-kanit="${esc(k)}">${esc(k.replaceAll("_"," "))}</button>`).join("")}</div></div>`).join("")}</div>`;
}
async function iddiaIsaretle(id,sonuc,el){
  try{
    await v2Post("/api/v2/iddia/isaretle",{id:id,sonuc:sonuc});
    if(SAHNE_AKTIF==="gecmis")await gecmisOkumalariYukle(true);
    else if(el){const nav=el.closest("nav");if(nav)nav.querySelectorAll("button").forEach(b=>b.classList.toggle("secili",b===el));}
  }catch(e){if(el)el.title=kullaniciyaHata(e);}
}
let GECMIS_OKUMALAR=null;
function gecmisTarih(ts){try{return new Date((+ts||0)*1000).toLocaleDateString("tr-TR",{year:"numeric",month:"short",day:"2-digit"});}catch(_e){return "—";}}
function gecmisOturumHtml(oturum,kayitlar){
  const ilk=kayitlar[0]||{}, yil=ilk.referans_yil?`SR ${ilk.referans_yil}`:"Yalnız Natal";
  return `<section class="gecmis-oturum"><header><div><span>${esc(gecmisTarih(ilk.ts))}</span><h3>${esc(yil)}</h3></div><small>${esc(String(oturum).slice(0,12))} · ${kayitlar.length} iddia</small></header>
    <div class="gecmis-iddialar">${kayitlar.map(i=>`<article><div><b>${esc(i.bolum||i.mercek||"—")}</b><p>${esc(i.iddia_metin||[i.davranis,i.alan,i.yon,i.zaman].filter(Boolean).join(" · "))}</p><small>${i.referans_yil?`referans ${esc(i.referans_yil)}`:"referans bugün / eski kayıt"}</small></div><nav>
      <button type="button" class="${i.sonuc==="tuttu"?"secili":""}" data-iddia-id="${esc(i.id)}" data-iddia-sonuc="tuttu">tuttu</button>
      <button type="button" class="${i.sonuc==="tutmadı"?"secili":""}" data-iddia-id="${esc(i.id)}" data-iddia-sonuc="tutmadı">tutmadı</button>
      <button type="button" class="${i.sonuc==="belirsiz"?"secili":""}" data-iddia-id="${esc(i.id)}" data-iddia-sonuc="belirsiz">belirsiz</button>
      ${i.sonuc?`<button type="button" class="geri" data-iddia-id="${esc(i.id)}" data-iddia-sonuc="geri_al">geri al</button>`:""}
    </nav></article>`).join("")}</div></section>`;
}
function gecmisOkumalarHtml(){
  const d=GECMIS_OKUMALAR||{}, tum=d.kayitlar||[];
  // Seans sırasında üretilen iddialar aynı ziyaret içinde işaretlenmez. Yeni
  // oturum açıldığında önceki oturum otomatik olarak "Geçmiş Okumalar"a düşer.
  const ls=OTURUM?tum.filter(x=>x.oturum!==OTURUM):tum;
  const gr={}; ls.slice().reverse().forEach(x=>(gr[x.oturum||"anon"]??=[]).push(x));
  const n=+d.brier_isaret||0, kalan=Math.max(0,30-n), genel=((d.brier||{}).genel||{});
  return `<div class="gecmis-hero"><span class="sahne-kicker">Geçmiş Okumalar · ${referansRozeti()}</span><h2>İddia ancak <em>sonradan</em> sınanır.</h2><p>Üretim anında puan verme yoktur. Eski oturumları burada topluca işaretle; yanlış tıklamayı geri alabilirsin.</p>
    <div class="brier-sayac"><b>${n}/30</b><span>${kalan?`Brier için ${kalan} kaldı`:`Brier yayımlanabilir · ${genel.brier!=null?`skor ${esc(genel.brier)}`:"ölçülüyor"}`}</span></div></div>
    ${Object.keys(gr).length?Object.entries(gr).map(([o,k])=>gecmisOturumHtml(o,k)).join(""):`<p class="sahne-sessiz">Önceki oturumdan işaretlenecek iddia yok. Bu seansta üretilen kayıtlar bir sonraki ziyarette görünür.</p>`}`;
}
async function gecmisOkumalariYukle(tazele=false){
  const ana=$("sahneAna"); if(!ana)return;
  if(!GECMIS_OKUMALAR||tazele){
    ana.innerHTML=`<p class="sahne-bekle">Geçmiş iddialar yükleniyor…</p>`;
    const r=await fetch("/api/v2/iddia/gecmis"); const d=await r.json();
    if(!r.ok)throw new Error(sunucuHatasi(d,r.status)); GECMIS_OKUMALAR=d;
  }
  ana.innerHTML=gecmisOkumalarHtml();
  ana.querySelectorAll("[data-iddia-id]").forEach(b=>b.onclick=()=>iddiaIsaretle(b.dataset.iddiaId,b.dataset.iddiaSonuc,b));
}

function sahneMercek(kod){
  const m=((SAHNE_ACILIS||{}).sahit||{}).mercekler||[];
  const es={hukum:"benlik",guc:"guc",gelisim:"gelisim",iliski:"iliski",is:"is",yer:"yer",zaman:"zaman"};
  return m.find(x=>x.kod===(es[kod]||kod))||null;
}
function sahneDurumRozeti(m){
  if(!m)return `<span class="sahne-durum sessiz">ölçülmedi</span>`;
  const c=m.celiskili?` · çelişkili`:``;
  return `<span class="sahne-durum ${esc(m.durum)}${m.celiskili?" celiskili":""}">${esc(m.durum)} · %${esc(m.belirginlik)}${c}</span>`;
}
function sahneGorevKarti(kod,acik=false){
  const g=(SAHNE_HARITA&&SAHNE_HARITA.gorevler||{})[kod]||{ad:kod};
  const m=sahneMercek(kod), x=SAHNE_SONUCLAR[kod];
  const kan=((SAHNE_ACILIS||{}).kanit||{})[kod]||[];
  return `<article class="sahne-gorev ${acik?"onerilen":""}" data-gorev-kart="${esc(kod)}">
    <div class="sg-bas"><div><span class="sg-kod">${esc(kod)}</span><h3>${esc(g.ad)}</h3></div>${sahneDurumRozeti(m)}</div>
    <p class="sg-ac">${m?esc(m.talimat):"Bu alan yalnız mevcut kanıt konuştuğunda açılır."}</p>
    <div class="sahit-rozetler">${sahneKanitHtml(kan)}</div>
    <div class="sg-sonuc" data-sg-sonuc="${esc(kod)}">${x?`${sahneMetaHtml(x)}${sahneMetinHtml(x)}`:""}</div>
    <button type="button" class="sahne-uret" data-v2bolum="${esc(kod)}">${x?"Yeniden yaz":"Bu alanı derinleştir"}</button>
  </article>`;
}
async function sahneBolumUret(kod,soru=""){
  const kart=document.querySelector(`[data-gorev-kart="${CSS.escape(kod)}"]`);
  const btn=kart&&kart.querySelector(".sahne-uret");
  const hedef=kart&&kart.querySelector(`[data-sg-sonuc="${CSS.escape(kod)}"]`);
  if(btn){btn.disabled=true;btn.textContent="Kanıtlar ayrıştırılıyor…";}
  if(hedef)hedef.innerHTML=`<div class="sahne-bekle"><span class="yaziyor"><i></i><i></i><i></i></span> Bu bölüm yalnız kendi bağlamıyla yazılıyor…</div>`;
  try{
    const d=await v2Post("/api/v2/bolum",{bolum:kod,soru:soru});
    SAHNE_SONUCLAR[kod]=d;
    if(hedef)hedef.innerHTML=sahneMetaHtml(d)+sahneMetinHtml(d);
    sahneButonlariniBagla(hedef);
    oturumYedekle();
    return d;
  }catch(e){
    if(hedef)hedef.innerHTML=`<p class="sahne-hata">${esc(kullaniciyaHata(e))}</p>`;
    return null;
  }finally{if(btn){btn.disabled=false;btn.textContent=SAHNE_SONUCLAR[kod]?"Yeniden yaz":"Tekrar dene";}}
}
function sahneButonlariniBagla(kok=document){
  kok.querySelectorAll("[data-v2bolum]").forEach(b=>b.onclick=()=>sahneBolumUret(b.dataset.v2bolum));
  kok.querySelectorAll(".sahit-rozet[data-kanit],.isnad-rozet[data-kanit]").forEach(b=>b.onclick=()=>{
    sahneGoster("rasathane",b.dataset.kanit);
  });
  kok.querySelectorAll("[data-iddia-id][data-iddia-sonuc]").forEach(b=>b.onclick=()=>iddiaIsaretle(b.dataset.iddiaId,b.dataset.iddiaSonuc,b));
}
function sahneHukum(){
  const ac=new Set((SAHNE_ACILIS||{}).acilacak||[]);
  const once=(((SAHNE_ACILIS||{}).sahit||{}).once||[]);
  const cel=(((SAHNE_ACILIS||{}).sahit||{}).celiskili||[]);
  const sess=(((SAHNE_ACILIS||{}).sahit||{}).sessiz||[]);
  const sic=(SAHNE_ACILIS||{}).sicil||{}, skon=(SAHNE_ACILIS||{}).sicil_konum||{};
  const se=(skon.eksenler||[]).slice().sort((a,b)=>(+b.yuzdelik||0)-(+a.yuzdelik||0))[0];
  return `<div class="sahne-hero">
    <div><span class="sahne-kicker">ŞAHİT-7 · kanıt ağı ${referansRozeti()}</span><h2>Danışanı önce <em>ayırt eden</em> şeyi bul.</h2>
      <p>Derinlik, her başlıkta konuşmak değil; bağımsız katmanların aynı davranışta birleştiği yerde ayrıntıya inmektir.</p></div>
    <div class="sahne-hero-ozet"><span>önce <b>${esc(once.join(" · ")||"—")}</b></span><span>çelişkili <b>${esc(cel.join(" · ")||"—")}</b></span><span>sessiz <b>${esc(sess.join(" · ")||"—")}</b></span><span>SİCİL <b>${esc(sic.n||0)}/${esc(sic.asgari||60)}</b>${se?` · ${esc(se.kod)} %${esc(se.yuzdelik)}`:""}</span></div>
  </div>
  <div class="sahne-gorev-grid">
    ${["hukum","guc","gelisim","iliski","is","yer"].map(k=>sahneGorevKarti(k,ac.has(k)||ac.has((({hukum:"benlik"})[k]||k)))).join("")}
  </div>
  <div class="sahne-cta"><div><b>Tek tek değil, bütün bir danışan dosyası mı?</b><span>Belge sahnesi sekiz yazı görevini sırayla üretir ve bölüm tekrarını ölçer.</span></div><button type="button" data-sahne-git="belge">Kanıtlı belgeye geç</button></div>`;
}
function sahneSoru(){
  const ss=(SAHNE_ACILIS||{}).sorular||[];
  return `<div class="sahne-hero dar"><div><span class="sahne-kicker">Soru sahnesi · ${referansRozeti()}</span><h2>Genel yorum değil, <em>tek soru</em>.</h2><p>Soru kendi kanıt kapsamıyla yanıtlanır; diğer bölümlerin anlatısını tekrar etmez.</p></div></div>
    <div class="soru-oneri">${ss.map(x=>`<button type="button" data-oneri-soru="${esc(x.soru||x.metin||x.ad||"")}">${esc(x.soru||x.metin||x.ad||"")}</button>`).join("")}</div>
    <article class="sahne-soru-kart" data-gorev-kart="soru">
      <textarea id="v2Soru" rows="4" placeholder="Danışanın gerçek sorusunu buraya yazın…"></textarea>
      <div class="sg-sonuc" data-sg-sonuc="soru">${SAHNE_SONUCLAR.soru?`${sahneMetaHtml(SAHNE_SONUCLAR.soru)}${sahneMetinHtml(SAHNE_SONUCLAR.soru)}`:""}</div>
      <button type="button" class="sahne-uret" id="v2SoruBtn">Soruyu kanıtla yanıtla</button>
    </article>`;
}
function ayTr(k){
  const A=["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"];
  const p=String(k||"").split("-"); return p.length>1?`${A[(+p[1]||1)-1]} ${p[0]}`:k;
}
function sahneZaman(){
  if(!SAHNE_ZAMAN)return `<div class="sahne-hero dar"><div><span class="sahne-kicker">Zaman sahnesi · ${referansRozeti()}</span><h2>Beş takvim değil, <em>tek omurga</em>.</h2><p>Natal ve Solar Return aynı olay üzerinde ayrı tartılır; algı eşiğinin altındaki gürültü şeride alınmaz.</p></div><button class="sahne-buyuk-btn" id="zamanYukle">12 aylık şeridi kur</button></div><div id="zamanBekle"></div>`;
  const aylar=SAHNE_ZAMAN.aylar||[];
  const zamanKatman=SAHNE_ZAMAN.solar_var?`SR ${esc(SAHNE_ZAMAN.solar_yil||"—")}`:"Yalnız Natal";
  return `<div class="sahne-hero dar"><div><span class="sahne-kicker">Zaman sahnesi · ${zamanKatman}</span><h2>On iki ayın <em>dokusu</em>.</h2><p>${esc(SAHNE_ZAMAN.yontem||"")}</p></div><div class="zaman-esik">görünürlük eşiği <b>${esc(SAHNE_ZAMAN.gorunurluk_esigi)}</b><small>${esc(SAHNE_ZAMAN.gizlenen_olay)} olay gürültü olarak süzüldü</small></div></div>
  <div class="zaman-serit-v2">${aylar.map((a,i)=>`<button type="button" class="zsv-ay ${i===0?"etkin":""}" data-zay="${i}" data-doku="${esc(a.doku)}">
    <span>${esc(ayTr(a.ay))}</span><b>${esc(a.yogunluk)}</b><i style="--y:${Math.max(2,+a.yogunluk||0)}%"></i><small>${esc(a.doku)}</small></button>`).join("")}</div>
  <div id="zamanAyDetay">${aylar.length?zamanAyDetay(aylar[0]):""}</div>`;
}
function zamanAyDetay(a){
  return `<article class="zaman-ay-detay"><div class="zad-bas"><div><span>${esc(ayTr(a.ay))}</span><h3>${esc(a.doku)}</h3></div><div class="zad-metrik"><b>${esc(a.yogunluk)}</b><span>yoğunluk</span><b>${esc(a.sessizlik)}</b><span>sessizlik</span><b>${esc(a.sikisma)}</b><span>sıkışma</span></div></div><p>${esc(a.cumle||"")}</p>
    ${(a.olaylar||[]).length?`<div class="zad-olaylar">${(a.olaylar||[]).slice(0,5).map(o=>`<span><b>${esc(o.tarih||"")}</b>${esc(o.tur||o.tip||o.ad||"olay")}${o.iki_harita?`<i>natal + solar</i>`:""}</span>`).join("")}</div>`:`<div class="sahne-sessiz">Eşiği aşan belirgin olay yok.</div>`}</article>`;
}
async function zamanYukle(){
  const b=$("zamanYukle"), w=$("zamanBekle"); if(b)b.disabled=true;
  if(w)w.innerHTML='<div class="sahne-bekle"><span class="yaziyor"><i></i><i></i><i></i></span> Natal ve Solar Return aynı zaman eksenine oturtuluyor…</div>';
  try{
    const dogum=(SON_MOD==="Kişisel")?girdiTopla():girdiTopla(false);
    const sv=(SON_ANALIZ&&SON_ANALIZ.solar_v2)||null;
    const srYil=(sv&&!sv.hata&&Number.isFinite(+sv.yil))?+sv.yil:null;
    // Yıl canlı formdan değil analiz oturumundan alınır. Form sonradan
    // değiştirilse bile Hüküm 2018 iken Zaman 2019'a kayamaz.
    if(srYil!==null)dogum.sr_year=srYil; else delete dogum.sr_year;
    SAHNE_ZAMAN=await v2Post("/api/v2/zaman",{dogum:dogum,ay_sayisi:12,
      solar_aktif:srYil!==null,year:srYil});
    sahneGoster("zaman");
  }catch(e){if(w)w.innerHTML=`<p class="sahne-hata">${esc(kullaniciyaHata(e))}</p>`;}
  finally{if(b)b.disabled=false;}
}
function sahneBelge(){
  const belge=SAHNE_SONUCLAR.__belge;
  if(!belge)return `<div class="belge-hero"><span class="sahne-kicker">Kanıtlı Danışan Dosyası · ${referansRozeti()}</span><h2>Danışanı parçalara ayırmadan, <em>sekiz ayrı mercekle</em> anlat.</h2><p>Her bölüm farklı bağlam ve farklı yazı biçimi kullanır. Önceki bölümlerin yalnız ilk iki cümlesi deftere girer; benzerlik eşiği aşılırsa bölüm bir kez yeniden yazılır. Veri sessizse metin icat edilmez.</p><button type="button" class="sahne-buyuk-btn" id="belgeUret">Derin danışan dosyasını üret</button><div id="belgeBekle"></div></div>`;
  const bol=belge.bolumler||[], top=+belge.toplam||8, biten=bol.length;
  const tekrarlar=bol.map(x=>+x.tekrar||0);
  const ort=tekrarlar.length?tekrarlar.reduce((a,b)=>a+b,0)/tekrarlar.length:0;
  const az=tekrarlar.length?Math.max(...tekrarlar):0;
  const isnadlar=bol.filter(x=>x.isnad_orani!=null).map(x=>+x.isnad_orani||0), isnad=isnadlar.length?isnadlar.reduce((a,b)=>a+b,0)/isnadlar.length:null;
  const hasvlar=bol.map(x=>+x.hasv_orani||0), hasv=hasvlar.length?hasvlar.reduce((a,b)=>a+b,0)/hasvlar.length:0;
  const durum=belge.uretimde
    ?`<div class="belge-ilerleme"><b>${biten}/${top}</b><span>${esc(belge.yazilan||"Hazırlanıyor…")}</span><i style="--p:${Math.round(biten/top*100)}%"></i></div>`
    :``;
  return `<div class="belge-hero hazir"><span class="sahne-kicker">Kanıtlı Danışan Dosyası · ${referansRozeti()}</span><h2>${belge.uretimde?"Dosya yazılırken okunabilir.":"Tekrarsız derin okuma."}</h2>${durum}<div class="belge-istat"><span>ortalama tekrar <b>%${Math.round(ort*100)}</b></span><span>azami tekrar <b>%${Math.round(az*100)}</b></span>${isnad!=null?`<span>isnâd <b>%${Math.round(isnad*100)}</b></span>`:""}<span class="${hasv>0?"uyari":""}">haşv <b>%${Math.round(hasv*100)}</b></span><span>bölüm <b>${biten}/${top}</b></span></div></div>
  <div class="belge-bolumler">${bol.map((x,i)=>`<article><span class="belge-sira">${String(i+1).padStart(2,"0")}</span><div><h3>${esc(x.baslik||x.bolum)}</h3>${sahneMetaHtml(x)}${sahneMetinHtml(x)}<div class="sahit-rozetler">${sahneKanitHtml(x.kanit||[])}</div></div></article>`).join("")}</div>
  ${belge.uretimde?`<div class="sahne-bekle"><span class="yaziyor"><i></i><i></i><i></i></span> ${esc(belge.yazilan||"Sıradaki mercek hazırlanıyor…")}</div>`:`<div class="belge-alt"><button type="button" id="belgeKopyala">Metni kopyala</button><span>Her bölüm yalnız kendi kanıtını görür; sessiz alan doldurulmaz.</span></div>`}`;
}
async function belgeUret(){
  const b=$("belgeUret"), w=$("belgeBekle");
  if(b){b.disabled=true;b.textContent="0/8 · Belge hazırlanıyor…";}
  if(w)w.innerHTML='<div class="sahne-bekle"><span class="yaziyor"><i></i><i></i><i></i></span> Bağlam bir kez hazırlanıyor…</div>';
  try{
    const bas=await v2Post("/api/v2/belge/baslat");
    const sira=bas.sira||[], toplam=+bas.toplam||sira.length||8;
    SAHNE_SONUCLAR.__belge={bolumler:[],toplam:toplam,uretimde:true,yazilan:"1/"+toplam+" · İlk mercek yazılıyor…"};
    sahneGoster("belge");
    for(let i=0;i<toplam;i++){
      const kod=sira[i]||"hukum";
      const g=(SAHNE_HARITA&&SAHNE_HARITA.gorevler||{})[kod]||{ad:kod};
      SAHNE_SONUCLAR.__belge.yazilan=`${i+1}/${toplam} · ${g.ad} yazılıyor…`;
      sahneGoster("belge");
      const cevap=await v2Post("/api/v2/belge/bolum",{sira:i+1});
      if(cevap&&cevap.bolum)SAHNE_SONUCLAR.__belge.bolumler.push(cevap.bolum);
      SAHNE_SONUCLAR.__belge.yazilan=(i+1<toplam)?`${i+2}/${toplam} · sıradaki mercek hazırlanıyor…`:`${toplam}/${toplam} · tamamlandı`;
      sahneGoster("belge");
      oturumYedekle();
    }
    SAHNE_SONUCLAR.__belge.uretimde=false;
    SAHNE_SONUCLAR.__belge.yazilan="";
    sahneGoster("belge");
    oturumYedekle();
  }catch(e){
    if(SAHNE_SONUCLAR.__belge)SAHNE_SONUCLAR.__belge.uretimde=false;
    sahneGoster("belge");
    const ana=$("sahneAna");
    if(ana)ana.insertAdjacentHTML("beforeend",`<p class="sahne-hata">${esc(kullaniciyaHata(e))}</p>`);
  }finally{if(b){b.disabled=false;b.textContent="Derin danışan dosyasını üret";}}
}

function belgeKopyala(){
  const b=SAHNE_SONUCLAR.__belge; if(!b)return;
  const t=(b.bolumler||[]).map(x=>`${x.baslik||x.bolum}\n${x.metin||""}`).join("\n\n");
  navigator.clipboard?.writeText(t).then(()=>{const x=$("belgeKopyala");if(x){x.textContent="Kopyalandı";setTimeout(()=>x.textContent="Metni kopyala",1400);}});
}
function rasathaneOdak(kanit){
  if(!kanit)return;
  const har={berzah_v2:"hukum",hukum:"hukum",yakinsama:"hareket_ozet",sarsma:"guven",cevaplanabilirlik:"guven",
    solar_v2:"zaman_ozet",human_design:"hd",kabzbast_v1_m66_74:"kabzbast",celiskiler:"celiski",direnc:"direnc",
    duraklama_izi:"duraklama",yas_katmani:"zaman_ozet",hamle_penceresi:"hareket_ozet",zaman_seridi:"lunasyon",
    kartografi:"kartografi",hudud_felek:"hudud",sinastri:"sinastri",davison:"davison",deklinasyon:"deklinasyon",kompozit:"kompozit"};
  const el=document.querySelector(`#sonuc .blok[data-kimlik="${CSS.escape(har[kanit]||kanit)}"]`);
  if(el){el.classList.remove("kapali","kategori-gizli");[...el.children].filter(c=>!c.classList.contains("blok-bas")).forEach(c=>c.style.display="");setTimeout(()=>el.scrollIntoView({behavior:"smooth",block:"center"}),120);}
}
function rasathaneReferansRozetleri(){
  const sinif=(SAHNE_HARITA&&SAHNE_HARITA.katman_siniflari)||{};
  const yil=((SON_ANALIZ&&SON_ANALIZ.referans)||{}).yil;
  const esleme={hukum:"berzah_v2",kutleler:"kutleler",hudud:"hudud_felek",kadim:"kadim_katman",
    hd:"human_design",deneme:"deneme_modulleri",guven:"sarsma",cevaplanabilirlik:"cevaplanabilirlik",
    duraklama:"duraklama_izi",donus:"donus_noktasi",sira:"sira_cevrimi",lunasyon:"lunasyon",
    sukut:"sukut",esik:"algi_esigi",kartografi:"kartografi.gunes_donusu",manevi:"maneviyat"};
  document.querySelectorAll("#sonuc .blok[data-kimlik]").forEach(bl=>{
    const kod=esleme[bl.dataset.kimlik]; if(!kod||!sinif[kod])return;
    const bas=bl.querySelector(".blok-bas"); if(!bas)return;
    bas.querySelectorAll(".katman-ref-rozet").forEach(x=>x.remove());
    const tur=sinif[kod];
    const et=tur==="natal_sabit"?"natal":tur==="daima_bugun"?"bugün":(yil?String(yil):"bugün");
    bas.insertAdjacentHTML("beforeend",`<span class="katman-ref-rozet ${esc(tur)}">${esc(et)}</span>`);
  });
}

function sahneGoster(kod,kanit=""){
  if(ROL!=="yonetici")return;
  SAHNE_AKTIF=kod; document.body.classList.add("sahne-aktif");
  document.body.classList.toggle("rasathane-goster",kod==="rasathane");
  const ana=$("sahneAna"), sonuc=$("sonuc");
  document.querySelectorAll("#sahneSekmeler button").forEach(b=>b.classList.toggle("etkin",b.dataset.sahne===kod));
  if(kod==="gecmis"){
    if(sonuc)sonuc.classList.remove("rasathane-acik");
    gecmisOkumalariYukle().catch(e=>{if(ana)ana.innerHTML=`<p class="sahne-hata">${esc(kullaniciyaHata(e))}</p>`;});
    return;
  }
  if(kod==="rasathane"){
    if(ana)ana.innerHTML=`<div class="rasathane-bas"><span class="sahne-kicker">Rasathane · ${referansRozeti()}</span><h2>Ölçüm konuşmaz; <em>kanıt gösterir.</em></h2><p>Bu çekmecedeki kartlarda AI düğmesi yoktur. Sahne metinlerinin arkasındaki ham hesap burada denetlenir.</p></div>`;
    if(sonuc){sonuc.classList.add("rasathane-acik");sonuc.querySelectorAll(".ai-dugme").forEach(x=>x.remove());rasathaneReferansRozetleri();}
    rasathaneOdak(kanit); return;
  }
  if(sonuc)sonuc.classList.remove("rasathane-acik");
  if(!ana)return;
  if(kod==="hukum")ana.innerHTML=sahneHukum();
  else if(kod==="soru")ana.innerHTML=sahneSoru();
  else if(kod==="zaman")ana.innerHTML=sahneZaman();
  else if(kod==="belge")ana.innerHTML=sahneBelge();
  sahneButonlariniBagla(ana);
  ana.querySelectorAll("[data-sahne-git]").forEach(b=>b.onclick=()=>sahneGoster(b.dataset.sahneGit));
  ana.querySelectorAll("[data-oneri-soru]").forEach(b=>b.onclick=()=>{if($("v2Soru"))$("v2Soru").value=b.dataset.oneriSoru;});
  if($("v2SoruBtn"))$("v2SoruBtn").onclick=()=>{const q=$("v2Soru").value.trim();if(q)sahneBolumUret("soru",q);};
  if($("zamanYukle"))$("zamanYukle").onclick=zamanYukle;
  ana.querySelectorAll("[data-zay]").forEach(b=>b.onclick=()=>{const i=+b.dataset.zay,a=(SAHNE_ZAMAN.aylar||[])[i];ana.querySelectorAll("[data-zay]").forEach(x=>x.classList.toggle("etkin",x===b));if(a&&$("zamanAyDetay"))$("zamanAyDetay").innerHTML=zamanAyDetay(a);});
  if($("belgeUret"))$("belgeUret").onclick=belgeUret;
  if($("belgeKopyala"))$("belgeKopyala").onclick=belgeKopyala;
}
async function defterYedekYukle(dosya){
  if(!dosya)return;
  try{
    const ham=await dosya.text(), veri=JSON.parse(ham);
    const r=await fetch("/api/v2/defter/iceri",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({veri,birlestir:true})});
    const x=await r.json(); if(!r.ok)throw new Error(sunucuHatasi(x,r.status));
    alert(`Defter birleştirildi. Yeni: ${Object.entries(x.yuklenen||{}).map(([k,v])=>`${k} ${v}`).join(" · ")||"0"}`);
    if(SONUC)await sahneKur(SONUC);
  }catch(e){alert(`Yedek yüklenemedi: ${kullaniciyaHata(e)}`);}
  finally{const f=$("defterYukleDosya");if(f)f.value="";}
}
function defterSeridiKur(df){
  const ds=$("defterSerit"); if(!ds)return;
  if(!df){ds.hidden=true;return;}
  const n=((df.sayilar||{}).iddia)||0;
  const uyari=df.sifirlanmis_olabilir
    ? "Defter sıfırlanmış olabilir — yedeği geri yükleyin."
    : df.yedek_hatirlat
      ? `${n} iddia kaydı birikti — saha yedeğini şimdi indirmeniz önerilir.`
      : "";
  if(!uyari){ds.hidden=true;return;}
  ds.hidden=false; ds.className=`ayar-serit defter-serit ${df.sifirlanmis_olabilir?"kaymis":""}`;
  ds.innerHTML=`<b>${df.sifirlanmis_olabilir?"DEFTER UYARISI":"YEDEK HATIRLATMASI"}</b><span>${esc(uyari)}</span><span class="defter-islem"><a class="mini-btn" href="/api/v2/defter/disaria">Yedeği indir</a><button type="button" class="mini-btn" id="defterYukleBtn">Yedeği yükle</button></span>`;
  const b=$("defterYukleBtn"),f=$("defterYukleDosya");
  if(b&&f)b.onclick=()=>f.click();
  if(f)f.onchange=()=>defterYedekYukle(f.files&&f.files[0]);
}
async function sahneKur(d){
  const kabuk=$("sahneKabuk"); if(!kabuk)return;
  if(ROL!=="yonetici"||!d){kabuk.hidden=true;document.body.classList.remove("sahne-aktif","rasathane-goster");return;}
  kabuk.hidden=false; document.body.classList.add("sahne-aktif");
  if($("sahneDanisan"))$("sahneDanisan").textContent=((d.girdi||{}).ad)||((d.girdi||{}).A||{}).ad||"Analiz";
  $("sonuc")?.querySelectorAll(".ai-dugme").forEach(x=>x.remove());
  if(SAHNE_YUKLENIYOR)return; SAHNE_YUKLENIYOR=true;
  try{
    const [h,a,ay,df]=await Promise.all([
      fetch("/api/v2/harita").then(async r=>{const x=await r.json();if(!r.ok)throw new Error(sunucuHatasi(x,r.status));return x;}),
      v2Post("/api/v2/acilis"),
      fetch("/api/v2/ayar/ozet").then(r=>r.ok?r.json():null).catch(()=>null),
      fetch("/api/v2/defter/ozet").then(r=>r.ok?r.json():null).catch(()=>null)
    ]);
    SAHNE_HARITA=h; SAHNE_ACILIS=a;
    const as=$("ayarSerit"); if(as&&ay){as.hidden=false;as.className=`ayar-serit ${esc(ay.durum||"")}`;as.innerHTML=`<b>${esc(ay.metin||"AYÂR")}</b><span>${ay.durum==="kaymis"?"Kalibrasyon referansını yenilemeyi değerlendirin.":ay.durum==="yetersiz_ornek"?"60 örnek dolmadan sapma hükmü verilmez.":"Referansın yaşayan örneklemle uyumu izleniyor."}</span>`;}
    defterSeridiKur(df);
    const nav=$("sahneSekmeler");
    nav.innerHTML=(h.sahneler||[]).map(x=>`<button type="button" data-sahne="${esc(x.kod)}">${esc(x.ad)}</button>`).join("")+
      `<button type="button" data-sahne="gecmis">Geçmiş Okumalar</button>`+
      `<button type="button" data-sahne="rasathane"><i class="rasat-nokta"></i>Rasathane</button>`;
    nav.querySelectorAll("button").forEach(b=>b.onclick=()=>sahneGoster(b.dataset.sahne));
    sahneGoster(SAHNE_AKTIF||"hukum");
    // Sonuç isteğinin dışındaki `display:block` satırı eski portal içindi.
    // Bir sonraki tikte Sahne'yi gerçek kaydırma hedefi yapıyoruz.
    setTimeout(()=>kabuk.scrollIntoView({behavior:"smooth",block:"start"}),80);
  }catch(e){
    $("sahneAna").innerHTML=`<p class="sahne-hata">Sahne kurulamadı: ${esc(kullaniciyaHata(e))}</p>`;
  }finally{SAHNE_YUKLENIYOR=false;}
}
