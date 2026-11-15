"""reference data: shipment statuses, service types, generic FAQ

Reference/configuration data required for the application to function. This is NOT demo data:
it contains no shipments, customers or company facts. All of it is editable by admins afterwards.

Shipment statuses and service names are short, common phrases, so they are seeded in every one of the
16 supported languages up front. FAQ answers are longer, more nuanced sentences, so only English and
French are pre-written here; other languages fall back to English on the public site until a staff
member adds a real translation through the FAQ admin page (see app.services.i18n.localized).

Revision ID: a1b2c3d4e5f6
Revises: 210616034248
"""
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "a1b2c3d4e5f6"
down_revision = "210616034248"
branch_labels = None
depends_on = None

LANGS = ("en", "fr", "es", "de", "pt", "it", "nl", "pl", "ru", "tr", "ar", "zh", "ja", "ko", "hi", "sw")

# code -> terminal, problem, notify, {lang: label}
STATUSES = [
    ("SHIPMENT_CREATED", False, False, True, {
        "en": "Shipment Created", "fr": "Expédition créée", "es": "Envío creado", "de": "Sendung erstellt",
        "pt": "Envio criado", "it": "Spedizione creata", "nl": "Zending aangemaakt", "pl": "Przesyłka utworzona",
        "ru": "Отправка создана", "tr": "Gönderi oluşturuldu", "ar": "تم إنشاء الشحنة", "zh": "货件已创建",
        "ja": "出荷を作成しました", "ko": "배송이 생성되었습니다", "hi": "शिपमेंट बनाया गया", "sw": "Shehena Imeundwa"}),
    ("PICKUP_SCHEDULED", False, False, True, {
        "en": "Pickup Scheduled", "fr": "Enlèvement planifié", "es": "Recogida programada", "de": "Abholung geplant",
        "pt": "Coleta agendada", "it": "Ritiro programmato", "nl": "Ophalen gepland", "pl": "Zaplanowano odbiór",
        "ru": "Забор запланирован", "tr": "Teslim alma planlandı", "ar": "تم تحديد موعد الاستلام", "zh": "取件已安排",
        "ja": "集荷予定", "ko": "픽업 예정", "hi": "पिकअप निर्धारित", "sw": "Ukusanyaji Umepangwa"}),
    ("PICKED_UP", False, False, True, {
        "en": "Picked Up", "fr": "Colis enlevé", "es": "Recogido", "de": "Abgeholt", "pt": "Coletado",
        "it": "Ritirato", "nl": "Opgehaald", "pl": "Odebrano", "ru": "Забрано", "tr": "Teslim alındı",
        "ar": "تم الاستلام", "zh": "已取件", "ja": "集荷済み", "ko": "픽업 완료", "hi": "उठाया गया", "sw": "Imekusanywa"}),
    ("ORIGIN_FACILITY", False, False, False, {
        "en": "Origin Facility", "fr": "Site d'origine", "es": "Instalación de origen", "de": "Ursprungsstandort",
        "pt": "Instalação de origem", "it": "Struttura di origine", "nl": "Vestiging van herkomst", "pl": "Placówka nadania",
        "ru": "Пункт отправления", "tr": "Çıkış tesisi", "ar": "منشأة المصدر", "zh": "始发地设施", "ja": "発送拠点",
        "ko": "출발지 시설", "hi": "मूल सुविधा", "sw": "Kituo cha Asili"}),
    ("PROCESSING", False, False, False, {
        "en": "Processing", "fr": "En traitement", "es": "En procesamiento", "de": "In Bearbeitung", "pt": "Em processamento",
        "it": "In elaborazione", "nl": "In behandeling", "pl": "W trakcie przetwarzania", "ru": "В обработке",
        "tr": "İşleniyor", "ar": "قيد المعالجة", "zh": "处理中", "ja": "処理中", "ko": "처리 중", "hi": "प्रक्रिया में",
        "sw": "Inashughulikiwa"}),
    ("DEPARTED_ORIGIN", False, False, True, {
        "en": "Departed Origin", "fr": "Parti de l'origine", "es": "Salió del origen", "de": "Herkunftsort verlassen",
        "pt": "Saiu da origem", "it": "Partito dall'origine", "nl": "Vertrokken bij herkomst", "pl": "Wysłano z miejsca nadania",
        "ru": "Отправлено из пункта отправления", "tr": "Çıkış noktasından ayrıldı", "ar": "غادر نقطة المصدر",
        "zh": "已从始发地发出", "ja": "発送拠点を出発", "ko": "출발지에서 출발함", "hi": "मूल स्थान से रवाना", "sw": "Imeondoka Asili"}),
    ("IN_TRANSIT", False, False, True, {
        "en": "In Transit", "fr": "En transit", "es": "En tránsito", "de": "Im Transit", "pt": "Em trânsito",
        "it": "In transito", "nl": "Onderweg", "pl": "W tranzycie", "ru": "В пути", "tr": "Transit halinde",
        "ar": "قيد النقل", "zh": "运输中", "ja": "輸送中", "ko": "운송 중", "hi": "पारगमन में", "sw": "Njiani"}),
    ("ARRIVED_AT_FACILITY", False, False, False, {
        "en": "Arrived at Facility", "fr": "Arrivé sur site", "es": "Llegó a la instalación", "de": "Am Standort angekommen",
        "pt": "Chegou à instalação", "it": "Arrivato alla struttura", "nl": "Aangekomen bij vestiging",
        "pl": "Przybyło do placówki", "ru": "Прибыло на объект", "tr": "Tesise ulaştı", "ar": "وصلت إلى المنشأة",
        "zh": "已到达设施", "ja": "拠点に到着", "ko": "시설 도착", "hi": "सुविधा पर पहुंचा", "sw": "Imewasili Kituo"}),
    ("CUSTOMS_CLEARANCE", False, False, True, {
        "en": "Customs/Clearance", "fr": "Douane / Dédouanement", "es": "Aduana / Despacho", "de": "Zoll/Abfertigung",
        "pt": "Alfândega / Liberação", "it": "Dogana / Sdoganamento", "nl": "Douane / Inklaring",
        "pl": "Cło / Odprawa", "ru": "Таможня / Очистка", "tr": "Gümrük / Gümrükleme", "ar": "الجمارك / التخليص",
        "zh": "清关", "ja": "税関手続き", "ko": "세관/통관", "hi": "सीमा शुल्क / निकासी", "sw": "Forodha/Kibali"}),
    ("DESTINATION_FACILITY", False, False, False, {
        "en": "Destination Facility", "fr": "Site de destination", "es": "Instalación de destino", "de": "Zielstandort",
        "pt": "Instalação de destino", "it": "Struttura di destinazione", "nl": "Vestiging van bestemming",
        "pl": "Placówka docelowa", "ru": "Пункт назначения", "tr": "Varış tesisi", "ar": "منشأة الوجهة",
        "zh": "目的地设施", "ja": "到着拠点", "ko": "목적지 시설", "hi": "गंतव्य सुविधा", "sw": "Kituo cha Mwisho"}),
    ("OUT_FOR_DELIVERY", False, False, True, {
        "en": "Out for Delivery", "fr": "En cours de livraison", "es": "En reparto", "de": "In Zustellung",
        "pt": "Saiu para entrega", "it": "In consegna", "nl": "Wordt afgeleverd", "pl": "W doręczeniu",
        "ru": "Доставляется", "tr": "Teslimat için yolda", "ar": "قيد التوصيل", "zh": "派送中", "ja": "配達中",
        "ko": "배송 중", "hi": "वितरण के लिए निकला", "sw": "Inasafirishwa kwa Uwasilishaji"}),
    ("DELIVERED", True, False, True, {
        "en": "Delivered", "fr": "Livré", "es": "Entregado", "de": "Zugestellt", "pt": "Entregue", "it": "Consegnato",
        "nl": "Afgeleverd", "pl": "Dostarczono", "ru": "Доставлено", "tr": "Teslim edildi", "ar": "تم التسليم",
        "zh": "已送达", "ja": "配達完了", "ko": "배송 완료", "hi": "वितरित", "sw": "Imewasilishwa"}),
    ("DELAYED", False, True, True, {
        "en": "Delayed", "fr": "Retardé", "es": "Retrasado", "de": "Verzögert", "pt": "Atrasado", "it": "In ritardo",
        "nl": "Vertraagd", "pl": "Zatrzymane", "ru": "Задержано", "tr": "Gecikti", "ar": "متأخر", "zh": "延误",
        "ja": "遅延", "ko": "지연됨", "hi": "देरी से", "sw": "Imechelewa"}),
    ("EXCEPTION", False, True, True, {
        "en": "Exception", "fr": "Incident", "es": "Incidencia", "de": "Ausnahme", "pt": "Ocorrência", "it": "Eccezione",
        "nl": "Uitzondering", "pl": "Wyjątek", "ru": "Инцидент", "tr": "İstisna", "ar": "استثناء", "zh": "异常",
        "ja": "例外", "ko": "예외 상황", "hi": "अपवाद", "sw": "Tatizo"}),
    ("CANCELLED", True, False, True, {
        "en": "Cancelled", "fr": "Annulé", "es": "Cancelado", "de": "Abgesagt", "pt": "Cancelado", "it": "Annullato",
        "nl": "Geannuleerd", "pl": "Odwołano", "ru": "Отменено", "tr": "İptal edildi", "ar": "ملغى", "zh": "已取消",
        "ja": "キャンセル済み", "ko": "취소됨", "hi": "रद्द", "sw": "Imeghairiwa"}),
]

SERVICES = [
    ("AIR_ Track", {
        "en": "Air  Track", "fr": "Fret aérien", "es": "Transporte aéreo", "de": "Luftfracht", "pt": "Frete aéreo",
        "it": "Trasporto aereo", "nl": "Luchtvracht", "pl": "Transport lotniczy", "ru": "Авиаперевозки",
        "tr": "Hava kargo", "ar": "الشحن الجوي", "zh": "空运", "ja": "航空貨物", "ko": "항공 화물", "hi": "हवाई माल ढुलाई",
        "sw": "Usafirishaji wa Anga"}),
    ("OCEAN_ Track", {
        "en": "Ocean  Track", "fr": "Fret maritime", "es": "Transporte marítimo", "de": "Seefracht",
        "pt": "Frete marítimo", "it": "Trasporto marittimo", "nl": "Zeevracht", "pl": "Transport morski",
        "ru": "Морские перевозки", "tr": "Deniz kargo", "ar": "الشحن البحري", "zh": "海运", "ja": "海上輸送",
        "ko": "해상 화물", "hi": "समुद्री माल ढुलाई", "sw": "Usafirishaji wa Baharini"}),
    ("ROAD_ Track", {
        "en": "Road  Track", "fr": "Fret routier", "es": "Transporte por carretera", "de": "Straßenfracht",
        "pt": "Frete rodoviário", "it": "Trasporto su strada", "nl": "Wegvervoer", "pl": "Transport drogowy",
        "ru": "Автомобильные перевозки", "tr": "Kara nakliyesi", "ar": "الشحن البري", "zh": "陆运", "ja": "陸上輸送",
        "ko": "육상 화물", "hi": "सड़क माल ढुलाई", "sw": "Usafirishaji wa Barabara"}),
    ("WAREHOUSING", {
        "en": "Warehousing", "fr": "Entreposage", "es": "Almacenamiento", "de": "Lagerung", "pt": "Armazenagem",
        "it": "Magazzinaggio", "nl": "Opslag", "pl": "Magazynowanie", "ru": "Складирование", "tr": "Depolama",
        "ar": "التخزين", "zh": "仓储", "ja": "倉庫保管", "ko": "창고 보관", "hi": "भंडारण", "sw": "Uhifadhi wa Ghala"}),
    (" Track_FORWARDING", {
        "en": " Track Forwarding", "fr": "Transit et affrètement", "es": "Transporte de carga",
        "de": "Spedition", "pt": "Despacho de carga", "it": "Spedizioni internazionali", "nl": "Expeditie",
        "pl": "Spedycja", "ru": "Экспедирование грузов", "tr": "Nakliye acenteliği", "ar": "الشحن والتوصيل",
        "zh": "货运代理", "ja": "貨物輸送代行", "ko": "화물 운송 대행", "hi": "माल अग्रेषण", "sw": "Uwakilishi wa Shehena"}),
    ("CUSTOMS_CLEARANCE", {
        "en": "Customs Clearance", "fr": "Dédouanement", "es": "Despacho de aduanas", "de": "Zollabfertigung",
        "pt": "Desembaraço aduaneiro", "it": "Sdoganamento", "nl": "Inklaring", "pl": "Odprawa celna",
        "ru": "Таможенное оформление", "tr": "Gümrükleme", "ar": "التخليص الجمركي", "zh": "清关服务",
        "ja": "税関通関", "ko": "통관", "hi": "सीमा शुल्क निकासी", "sw": "Kibali cha Forodha"}),
]

FAQS = [
    ("Where do I find my tracking number?",
     "Your tracking number is on your shipping confirmation and on the paperwork you received when the shipment was booked. If you cannot find it, contact us with your reference number.",
     "Où trouver mon numéro de suivi ?",
     "Votre numéro de suivi figure sur votre confirmation d'expédition et sur les documents remis lors de la réservation. Si vous ne le trouvez pas, contactez-nous avec votre numéro de référence."),
    ("Why does my tracking number show as not found?",
     "Check that you typed the number exactly as shown. A shipment may also take a short time to appear after it is booked. If the problem continues, please contact us.",
     "Pourquoi mon numéro de suivi est-il introuvable ?",
     "Vérifiez que le numéro est saisi exactement comme indiqué. Une expédition peut aussi mettre un court instant à apparaître après sa réservation. Si le problème persiste, contactez-nous."),
    ("How often is tracking information updated?",
     "Tracking updates when our team records a new event for your shipment, such as a change of status or location. Delivery estimates can change and are not guaranteed.",
     "À quelle fréquence le suivi est-il mis à jour ?",
     "Le suivi est mis à jour lorsque notre équipe enregistre un nouvel événement pour votre expédition, comme un changement de statut ou de lieu. Les estimations de livraison peuvent changer et ne sont pas garanties."),
    ("How do I request a quote?",
     "Use the Request a Quote form and tell us where the cargo is going, what it is and roughly how much there is. Our team will contact you.",
     "Comment demander un devis ?",
     "Utilisez le formulaire de demande de devis et indiquez la destination, la nature et la quantité approximative de la marchandise. Notre équipe vous contactera."),
]


def upgrade() -> None:
    statuses = sa.table("shipment_statuses", sa.column("code"), sa.column("label", JSONB), sa.column("sort_order"),
                        sa.column("is_terminal"), sa.column("is_problem"), sa.column("is_active"), sa.column("notify_customer"))
    op.bulk_insert(statuses, [
        dict(code=code, label=label, sort_order=(i + 1) * 10, is_terminal=term, is_problem=prob, is_active=True, notify_customer=notify)
        for i, (code, term, prob, notify, label) in enumerate(STATUSES)
    ])
    services = sa.table("service_types", sa.column("id", sa.UUID), sa.column("code"), sa.column("name", JSONB),
                        sa.column("is_active"), sa.column("sort_order"))
    op.bulk_insert(services, [
        dict(id=uuid.uuid4(), code=code, name=name, is_active=True, sort_order=(i + 1) * 10)
        for i, (code, name) in enumerate(SERVICES)
    ])
    faqs = sa.table("faqs", sa.column("id", sa.UUID), sa.column("question", JSONB), sa.column("answer", JSONB),
                    sa.column("sort_order"), sa.column("is_published"))
    op.bulk_insert(faqs, [
        dict(id=uuid.uuid4(), question={"en": qe, "fr": qf}, answer={"en": ae, "fr": af}, sort_order=(i + 1) * 10, is_published=True)
        for i, (qe, ae, qf, af) in enumerate(FAQS)
    ])


def downgrade() -> None:
    op.execute("DELETE FROM faqs")
    op.execute("DELETE FROM service_types WHERE code IN ('AIR_ Track','OCEAN_ Track','ROAD_ Track','WAREHOUSING',' Track_FORWARDING','CUSTOMS_CLEARANCE')")
    op.execute("DELETE FROM shipment_statuses WHERE code IN (%s)" % ",".join(f"'{s[0]}'" for s in STATUSES))
