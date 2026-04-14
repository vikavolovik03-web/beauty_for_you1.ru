"""
BEAUTY FOR YOU - Интернет-магазин косметики
Flask приложение с каталогом, корзиной и админ-панелью
"""

# === ИМПОРТЫ ===
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

# === НАСТРОЙКИ ===
app = Flask(__name__) 
app.config.update(
    SECRET_KEY='beauty-for-you-secret-key-2024',
    SQLALCHEMY_DATABASE_URI='sqlite:///beauty_shop.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SEND_FILE_MAX_AGE_DEFAULT=0,
)

# === ИНИЦИАЛИЗАЦИЯ ===
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# === ФИЛЬТР ДЛЯ ШАБЛОНОВ ===
@app.template_filter('from_json')
def from_json_filter(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

# ==================== МОДЕЛИ БАЗЫ ДАННЫХ ====================

# Модель для обращений с контактной страницы
class ContactMessage(db.Model):
    __tablename__ = 'contact_message' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

# Модель пользователя
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cart_items = db.relationship('CartItem', back_populates='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='user', lazy=True)

    def get_cart_total(self):
        return sum(item.quantity for item in self.cart_items)

# Модель товара
class Product(db.Model):
    __tablename__ = 'product' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float)
    image = db.Column(db.String(200), default='default.jpg')
    images_list = db.Column(db.Text)  
    description = db.Column(db.Text)
    composition = db.Column(db.Text)
    usage = db.Column(db.Text)
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def images_list_parsed(self):
        try:
            return json.loads(self.images_list) if self.images_list else []
        except:
            return []

# Модель элемента корзины
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='cart_items')
    product = db.relationship('Product', backref='cart_items')

# Модель заказа
class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120))
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_method = db.Column(db.String(50), default='courier')
    payment_method = db.Column(db.String(50), default='cash')
    total_amount = db.Column(db.Float, nullable=False)
    items_json = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='new')
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ← Используем back_populates
    user = db.relationship('User', back_populates='orders')

    def items_parsed(self):
        try:
            return json.loads(self.items_json) if self.items_json else []
        except:
            return []

# Модель элемента заказа
class OrderItem(db.Model):
    __tablename__ = 'order_item'  # ← Исправлено
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    subtotal = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')

# Создаем таблицы
with app.app_context():
    db.create_all()

# ==================== НАПОЛНЕНИЕ БД ====================

def init_db():
    with app.app_context():
        db.create_all()
        if Product.query.first(): return
        
        print("📦 Наполнение БД...")
        products = [
             # === Уход за волосами ===
            Product(
                name="Восстанавливающая сыворотка для волос",
                brand="D'ALBA",
                price=2590,
                old_price=2890,
                category="Волосы",
                description="Ухаживающая спрей сыворотка для волос c нежным цветочным ароматом обладает увлажняющими и питательными свойствами, укрепляет волосы и придает им сияющий и здоровый вид. Содержит в составе шелковый протеин, кератин, 20 видов аминокислот для укрепления сухих и ломких волос. Средство быстро впитывается в волосы, делая их мягкими и послушными, оставляя только приятный аромат.",
                composition="Water, Cyclopentasiloxane, Cyclohexasiloxane, Dimethicone, 1,2-Hexanediol, Propanediol, Dipropylene Glycol, Fragrance, Sodium Chloride, Butylene Glycol, Sodium Citrate, Citric Acid, Tocopheryl Acetate, Eclipta Prostrata Extract, Disodium EDTA, Xanthan Gum, Melia Azadirachta Leaf Extract, Argania Spinosa Kernel Oil, Macadamia Ternifolia Seed Oil, Oenothera Biennis (Evening Primrose) Oil, Simmondsia Chinensis (Jojoba) Seed Oil, Camellia Japonica Seed Oil, Hydrolyzed Keratin, Tuber Magnatum Extract, Moringa Oleifera Seed Oil, Glycine, Serine, Glutamic Acid, Silk Extract, Aspartic Acid, Leucine, Alanine, Adansonia Digitata Seed Oil, Camellia Oleifera Seed Oil, Carthamus Tinctorius (Safflower) Seed Oil, Helianthus Annuus (Sunflower) Seed Oil, Hippophae Rhamnoides Oil, Olea Europaea (Olive) Fruit Oil, Persea Gratissima (Avocado) Oil, Prunus Armeniaca (Apricot) Kernel Oil, Ribes Nigrum (Black Currant) Seed Oil, Lysine, Arginine, Tyrosine, Phenylalanine, Threonine, Valine, Proline, Isoleucine, Histidine, Methionine, Cysteine, Ethylhexylglycerin, Tocopherol, Magnesium PCA, Sodium Lactate, Copper Tripeptide-1, Sucrose, Urea, Calcium Chloride, Potassium Hydroxide, Ornithine, Sea Salt, Magnesium Chloride, Dipotassium Phosphate, Magnesium Citrate, Glucosamine HCl, 1-Methylhydantoin-2-Imide, Asparagine, Citrulline, Uric Acid, Taurine, Tryptophan, Formic Acid, Ammonia, Glutamine, Limonene, Linalool, Butylphenyl Methylpropional, Benzyl Benzoate, Geraniol, Hexyl Cinnamal",
                usage="Встряхните флакон 2-3 раза, затем распылите средство на влажные или сухие волосы. Не требует смывания.",
                image="dalba_serum.jpg",
                images_list='["dalba_serum_2.jpg", "dalba_serum_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Сыворотка для выпрямления волос",
                brand="ARAVIA",
                price=514,
                old_price=650,
                category="Волосы",
                description="Многофункциональная сыворотка предназначена для комплексного ухода за волосами. Сыворотка обладает моментальным и накопительным эффектом.",
                composition="Aqua, Glycerin, Phenoxyethanol, Cetrimonium Chloride, Polyquaternium-37, Guar Hydroxypropyltrimonium Chloride, PEG-12 Dimethicone, Parfum, Hydrolyzed Keratin, Ethylhexylglycerin, Citric Acid, Potassium Sorbate",
                usage="Равномерно нанесите небольшое количество сыворотки на влажные волосы, избегая прикорневой зоны. Не требует смывания. Рекомендуется для регулярного применения.",
                image="aravia_straight.jpg",
                images_list='["aravia_straight_2.jpg", "aravia_straight_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Масло для кончиков волос",
                brand="D'ALBA",
                price=1890,
                category="Волосы",
                description="Увлажняющее масло для кончиков придает волосам блеск и гладкость, препятствует запутыванию и сечениюВ составе продукта комплекс природных масел арганы, хлопка и виноградной косточки.",
                composition="Cyclopentasiloxane, Isopropyl Myristate, Dimethicone, Bis-Diisopropanolamino-PG-Propyl Disiloxane/Bis-Vinyl Dimethicone Copolymer, Gossypium Herbaceum (Cotton) Seed Oil, Argania Spinosa Oil, Vitis Vinifera Seed Oil, Fragrance.",
                usage="Просто нанесите небольшое количество масло на ладони и проведите по длине чистых, подсушенных волос, особое внимание уделяя кончикам. Избегайте корни и прикорневую зону роста волос..",
                image="dalba_oil.jpg",
                in_stock=True
            ),
            Product(
                name="Шампунь восстанавливающий",
                brand="HADAT COSMETICS",
                price=2190,
                category="Волосы",
                description="Шампунь на основе минералов и соли мертвого моря глубоко очищают кожу головы, борются с излишней жирностью и как следствие, образованием перхоти. Успокаивают зуд, восстанавливают и нормализуют естественный микробиом, устраняют шелушения на коже головы.",
                composition="WATER, (AQUA) SODIUM DODECYL SULFONATE, AMMONIUM LAURETH SULFATE, LAURAMIDE DEA, LIMUS (DEAD SEA MUD), OLEA EUROPAEA (OLIVE) FRUIT OIL, LINUM USITATISSIMUM (FLAX) SEED OIL, DIMETHICONE, HEDROLIZED KERATIN, FRAGRANCE, MARIS SAL (DEAD SEA),SODIUM STYRENE/ ACRYLATES COPOLYMER, DMDM-H, IMIDAZOLIDINYL UREA, PHENOXYETHANOL, BENZOIC ACID, D-PANTHENOL, ALOE BARBADENSIS EXTRACT, CITRIC ACID, TOCOPHERYL ACETATE, HYDROXYCITRONALLAL, GERANIOL, LINALOOL, BENZYL SALICILAYTE, COUMARIN, CITRONELLOL, LIMONENE, ALPHA-ISOMETHYL IONONE, BENZYL BENZOATE, CITRAL, EUGENOL.",
                usage="Нанесите небольшое количество шампуня на влажные волосы, помассируйте от корней до кончиков. Смойте. При необходимости повторите.",
                image="dalba_shampoo.jpg",
                images_list='["dalba_shampoo_2.jpg", "dalba_shampoo_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Маска для волос глубокого восстановления",
                brand="ARAVIA LABORATORIES",
                price=890,
                old_price=1100,
                category="Волосы",
                description="Нанесите маску на чистые влажные волосы по всей длине, избегая корней. Оставьте на 15-20 минут. Смойте маску теплой водой.",
                composition="Aqua, Vitis Vinifera (Grape) Seed Oil, Cetearyl Alcohol, Glycerin, Dipalmitoylethyl Hydroxyethylmonium Methosulfate, Cyclopentasiloxane, Cetrimonium Chloride, Bis(C13-15 Alkoxy) PG-Amodimethicone, Ceteareth-20, Panthenol, Polyquaternium-37, C14-15 Alcohols, Dimethiconol, Guar Hydroxypropyltrimonium Chloride, Parfum, Hydrolyzed Collagen, Citric Acid, Hydrolyzed Keratin, BHT, Isotridecyl Alcohol, Phenoxyethanol, Methylchloroisothiazolinone, Potassium Sorbate, Methylisothiazolinone",
                usage="Нанесите на чистые влажные волосы на 5-10 минут. Смойте тёплой водой. 1-2 раза в неделю.",
                image="aravia_mask.jpg",
                images_list='["aravia_mask_2.jpg", "aravia_mask_3.jpg"]',
                in_stock=True
            ),
            
            # === Уход за лицом ===
            Product(
                name="Масло очищающее",
                brand="SHISEIDO",
                price=4537,
                category="Лицо",
                description="Масло позволяет мгновенно очистить кожу лица от стойкого макияжа: тональные средства на масляной основе, водостойкая тушь, карандаш для глаз, которые не всегда легко удалить с помощью обычных средств для снятия макияжа.",
                composition="PARAFFINUM LIQUIDUM, PEG-8 GLYCERYL ISOSTEARATE, CETYL ETHYLHEXANOATE, ISODODECANE, AQUA, ISOSTEARIC ACID, GLYCERIN, ALCOHOL DENAT., VITIS VINIFERA (GRAPE) SEED OIL, PARFUM, BHT, TOCOPHEROL",
                usage="Нажмите на дозатор три раза, нанесите средство на ладонь, затем равномерно распределите по поверхности кожи. Смойте прохладной или теплой водой.",
                image="shiseido_oil.jpg",
                in_stock=True
            ),
            Product(
                name="Гель для умывания",
                brand="ARAVIA LABORATORIES",
                price=644,
                old_price=790,
                category="Лицо",
                description="Энзимный гель глубоко и бережно очищает кожу от последствий воздействия окружающей среды, отшелушивает омертвевшие клетки, выравнивает рельеф и стимулирует обновление клеток эпидермиса. Разглаживает морщины, повышает упругость и эластичность. Делает кожу гладкой и бархатистой, возвращает сияние и улучшает внешний вид.",
                composition="Aqua, Cocamidopropyl Betaine, Coco-Glucoside, Disodium Laureth Sulfosuccinate, Laureth-2, PEG/PPG-120/10 Trimethylolpropane Trioleate, Parfum, Papain, Ananas Sativus Fruit Extract, Citrus Limon Fruit Extract, Panax Ginseng Root Extract, Zingiber Officinale Root Extract, Citric Acid, CI 19140, Methylchloroisothiazolinone, Methylisothiazolinone, CI 16185",
                usage="Нанесите гель легкими массирующими движениями на очищенную от макияжа и подготовленную кожу. Оставьте на 10 минут. Тщательно смойте теплой водой. Рекомендуется использовать 1-2 раза в неделю.",
                image="aravia_gel.jpg",
                images_list='["aravia_gel_2.jpg", "aravia_gel_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Очищающий гель для кожи лица",
                brand="BIODERMA",
                price=1100,
                category="Лицо",
                description="Гель для умывания Bioderma Sensibio мягко очищает кожу, даже самую чувствительную, в том числе и область вокруг глаз. Не вызывает раздражения. Со временем кожа становится менее реактивной, более увлажненной и защищенной от негативного воздействия свободных радикалов.",
                composition="AQUA/WATER/EAU, SODIUM COCOAMPHOACETATE, PROPANEDIOL, SODIUM LAUROYL SARCOSINATE, CITRIC ACID, COCO-GLUCOSIDE, GLYCERYL OLEATE, SODIUM CITRATE, PEG-90 GLYCERYL ISOSTEARATE, MANNITOL, XYLITOL, LAURETH-2, RHAMNOSE, FRUCTOOLIGOSACCHARIDES, TOCOPHEROL, HYDROGENATED PALM GLYCERIDES CITRATE, LECITHIN, ASCORBYL PALMITATE.",
                usage="Вспенить в руках, нанести на влажную кожу, помассировать и тщательно смыть водой. Использовать утром и / или вечером.",
                image="bioderma_gel.jpg",
                images_list='["bioderma_gel_2.jpg", "bioderma_gel_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Скраб-эксфолиант для глубокого очищения",
                brand="ARAVIA LABORATORIES",
                price=591,
                old_price=750,
                category="Лицо",
                description="Скраб-эксфолиант обеспечивает мгновенный детокс и глубокое очищение кожи головы от загрязнений окружающей среды, избытка себума и остатков укладочных средств. АНА-кислоты отшелушивают ороговевший слой кожи, благодаря чему происходит обновление клеток и нормализуется выделение себума.",
                composition="Aqua, Silica, Cetearyl Alcohol, Glyceryl Stearate, Cocos Nucifera Seed Butter, Glycerin, PEG-100 Stearate, Coco-Glucoside, Crambe Abyssinica Seed Oil, Phenoxyethanol, Tocopheryl Acetate, Methylparaben, Glycolic Acid, Parfum, BHT, Propylparaben, DMDM Hydantoin, Ethylparaben",
                usage="Перед использованием шампуня нанесите скраб на влажную кожу головы, разделяя волосы на проборы. Проведите легкий массаж. Рекомендуется использовать 1-2 раза в неделю.",
                image="aravia_scrub.jpg",
                images_list='["aravia_scrub_2.jpg", "aravia_scrub_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Тоник увлажняющий",
                brand="BIODERMA",
                price=950,
                category="Лицо",
                description="Тоник глубоко увлажняет, смягчает и защищает кожу от потери влаги в течение длительного времени. Защищает от негативного воздействия окружающей среды, убирает следы усталости, дарит здоровый цвет лица и возвращает сияние. Омолаживает, повышает упругость и эластичность, укрепляет кожу. Восстанавливает нормальный уровень рН.",
                composition="Aqua, Centaurea Cyanus Flower Water, Glycerin, Phenoxyethanol, Betaine, Panthenol, Ethylhexylglycerin, Centella Asiatica Extract, PEG-40 Hydrogenated Castor Oil, Salvia Hispanica Herb Extract, Disodium EDTA, Parfum, Sodium Hyaluronate",
                usage="Нанесите тоник при помощи ватного диска на чистую кожу лица и шеи. Использовать 1-2 раза в день.",
                image="bioderma_tonic.jpg",
                images_list='["bioderma_tonic_2.jpg", "bioderma_tonic_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Крем увлажняющий дневной",
                brand="SHISEIDO",
                price=3890,
                old_price=4500,
                category="Лицо",
                description="Больше, чем просто увлажнение. Постоянный источник свежести и здорового сияния для вашей кожи.",
                composition="INGREDIENTS:WATER(AQUA/EAU)･ALCOHOL DENAT.･DIMETHICONE･GLYCERIN･HOMOSALATE･ETHYLHEXYL SALICYLATE･OCTOCRYLENE･DIPROPYLENE GLYCOL･ISODECYL NEOPENTANOATE･BUTYL METHOXYDIBENZOYLMETHANE･PEG-20･POLYSILICONE-15･BEHENYL ALCOHOL･DIGLYCERIN･SILICA･PHENOXYETHANOL･POLYSILICONE-11･AMMONIUM ACRYLOYLDIMETHYLTAURATE/BEHENETH-25 METHACRYLATE CROSSPOLYMER･BATYL ALCOHOL･BUTYLENE GLYCOL･BIS-BUTYLDIMETHICONE POLYGLYCERYL-3･CHLORPHENESIN･CARBOMER･POTASSIUM HYDROXIDE･ERYTHRITOL･PEG/PPG-14/7 DIMETHYL ETHER･PEG/PPG-17/4 DIMETHYL ETHER･FRAGRANCE (PARFUM)･PEG-60 GLYCERYL ISOSTEARATE･LAURYL BETAINE･ALCOHOL･TOCOPHEROL･BHT･ACRYLATES/C10-30 ALKYL ACRYLATE CROSSPOLYMER･2-O-ETHYL ASCORBIC ACID･XANTHAN GUM･SODIUM METABISULFITE･CAFFEINE･ISOSTEARIC ACID･SODIUM METAPHOSPHATE･DISODIUM EDTA･PPG-3 DIPIVALATE･PHYTOSTERYL MACADAMIATE･LINALOOL･IRON OXIDES (CI 77492)･LIMONENE･CITRUS UNSHIU PEEL EXTRACT･SODIUM HYALURONATE･ANGELICA KEISKEI LEAF/STEM EXTRACT･ZIZIPHUS JUJUBA FRUIT EXTRACT･PANAX GINSENG ROOT EXTRACT･SODIUM ACETYLATED HYALURONATE･IRON OXIDES (CI 77491)･SCUTELLARIA BAICALENSIS ROOT EXTRACT･SYZYGIUM JAMBOS LEAF EXTRACT･ALPINIA SPECIOSA LEAF EXTRACT･SODIUM BENZOATE･ROSMARINUS OFFICINALIS (ROSEMARY) LEAF EXTRACT (ROSMARINUS OFFICINALIS LEAF EXTRACT)･SANGUISORBA OFFICINALIS ROOT EXTRACT･PYROLA INCARNATA EXTRACT･",
                usage="Нанесите на очищенную кожу лица утром. Избегайте области вокруг глаз.",
                image="shiseido_cream.jpg",
                images_list='["shiseido_cream_2.jpg", "shiseido_cream_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Сыворотка с витамином С",
                brand="D'ALBA",
                price=2890,
                category="Лицо",
                description="Сыворотка с 3D витамином С – насыщенный антиоксидантами витаминный коктейль, заряжающий кожу энергией и сиянием. Благодаря 3-м видам витамина С и пептидам, сыворотка выравнивает и улучшает цвет лица, дарит коже яркость и здоровое сияние, стирает признаки усталости, предотвращает преждевременное старение кожи.",
                composition="Aqua, Niacinamide, 3-O-Ethyl Ascorbic Acid, Ascorbyl Tetraisopalmitate, C13-15 Alkane, Pentylene Glycol, Glycerin, Terminalia Ferdinandiana Fruit Extract, Tetradecyl Aminobutyroyl- valylaminobutyric Urea Trifluoroacetate, Palmitoyl Tripeptide-5, Palmitoyl Dipeptide-5 Diaminobutyroyl Hydroxythreonine, Acer Rubrum Extract, Arachidyl Alcohol, Behenyl Alcohol, Arachidyl Glucoside, Sodium Hyaluronate, Ectoin, Tocopherol (mixed), Beta Sitosterol, Squalene, Caprylyl Glycol, Benzyl Alcohol, Sodium Acrylates Copolymer, Lecithin, Lactic Acid, Parfum, D-Limonene, Butylphenyl Methylpropional, Hexyl Cinnamal.",
                usage="Нанести небольшое количество сыворотки на сухую, предварительно очищенную кожу. В случае необходимости можно использовать крем, подходящий вашему типу кожи, после нанесения сыворотки. Для оптимального результата рекомендуется применять сыворотку не менее двух месяцев.",
                image="dalba_vitamin_c.jpg",
                images_list='["dalba_vitamin_c_2.jpg", "dalba_vitamin_c_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Ночной крем восстанавливающий",
                brand="ARAVIA LABORATORIES",
                price=1250,
                category="Лицо",
                description="Крем с азелаиновой кислотой (5%) помогает коже справиться с недостатками и улучшить ее состояние и внешний вид. Азелаиновая кислота оказывает мощное противовоспалительное и себорегулирующее действие, борется с акне и черными точками. Нормализует процессы регенерации клеток, выравнивает и разглаживает поверхность кожи. Обладает осветляющим эффектом, помогает минимизировать следы постакне, устраняет пигментацию и покраснения. В результате курсового использования позволяет забыть про неровный тон и тусклость кожи.",
                composition="Aqua, Isopentyldiol, Polyquaternium-37, Azelaic acid, Triethanolamine, Allantoin, Phenoxyethanol (and) Ethylhexylglycerin, Perfume.",
                usage="Нанесите крем на предварительно очищенную кожу. Рекомендуется использовать 2 раза в день курсом в течение 1 месяца или в качестве SOS-средства.",
                image="aravia_night.jpg",
                images_list='["aravia_night_3.jpg"]',
                in_stock=True
            ),
            
            # === Уход за телом ===
            Product(
                name="Медовое молочко для тела с экстрактом жемчуга",
                brand="HEMPZ",
                price=650,
                old_price=850,
                category="Тело",
                description="Hempz Sweet Pineapple & Honey Melon Herbal Body Moisturizer - молочко с формулой, созданной на основе комплекса MIRACLEOILBLEND (ЧУДО-МАСЛО), объединяющей несколько видов натуральных растительных масел для эффективного увлажнения и сохранения влаги. Смягчает, разглаживает и обновляет сухую кожу. ",
                composition="Water/Aqua/Eau, Isopropyl Palmitate, Butylene Glycol, Propanediol, Glycerin, Butyrospermum Parkii (Shea) Butter, Dimethicone, Sorbitan Stearate, Fragrance (Parfum), Stearic Acid, Glyceryl Stearate, PEG-100 Stearate, Cannabis Sativa Seed Oil, Ananas Sativus (Pineapple) Fruit Extract, Calendula Officinalis Flower Extract, Cucumis Melo (Melon) Fruit Extract, Zingiber Officinale (Ginger) Root Extract, Cocos Nucifera (Coconut) Oil, Persea Gratissima (Avocado) Oil, Simmondsia Chinensis (Jojoba) Seed Oil, Aloe Barbadensis Leaf Juice, Chamomilla Recutita (Matricaria) Flower Extract, Cucumis Sativus (Cucumber) Fruit Extract, Helianthus Annuus (Sunflower) Seed Oil, Althaea Officinalis Root Extract, Panax Ginseng Root Extract, Symphytum Officinale Leaf Extract, Phenoxyethanol, Cetyl Alcohol, Nylon-12, Polysorbate 40, Limonene, Chlorphenesin, Carbomer, Aminomethyl Propanol, Ethylhexylglycerin, Tocopheryl Acetate, Disodium EDTA, Benzyl Benzoate, Linalool, Tocopherol, Yellow 5 (CI 19140), Yellow 6 (CI 15985), Ascorbic Acid, Retinyl Palmitate, Red 40 (CI 16035), Citric Acid, Potassium Sorbate, Sodium Benzoate",
                usage="Распределите молочко по всему телу, мягко массируя круговыми движениями до полного впитывания. Используйте его после купания или в любой момент для укрепления защитного барьера кожи и придания ей нежности и свежести.",
                image="honey_milk.jpg",
                images_list='["honey_milk_2.jpg", "honey_milk_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Скраб для тела кофейный",
                brand="ARAVIA LABORATORIES",
                price=790,
                category="Тело",
                description="Антицеллюлитный эффект, улучшение микроциркуляции. С кофейными зёрнами.",
                composition="Кофеин, молотые кофейные зёрна, масло ши, витамин E",
                usage="Нанесите на влажную кожу, помассируйте проблемные зоны. Смойте водой. 2-3 раза в неделю.",
                image="aravia_coffee.jpg",
                images_list='["aravia_coffee_2.jpg", "aravia_coffee_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Крем для рук восстанавливающий",
                brand="BIODERMA",
                price=450,
                category="Тело",
                description="Смягчающий шоколадный крем-скраб на основе натуральных молотых какао-бобов для мягкого очищения от загрязнений и отшелушивания ороговевших клеток. Стимулирует процесс регенерации, выравнивает общий тон кожи, повышает её эластичность. Масло сладкого миндаля смягчает, омолаживает кожу, насыщая ее витаминами и жирными кислотами. Экстракт ламинарии и масло зеленого кофе активируют лимфодренаж и помогают в борьбе с лишними сантиметрами и целлюлитом. Скраб обеспечивает общий укрепляющий эффект, оставляя кожу гладкой и сияющей. Пленительный аромат шоколада поднимает настроение и делает процедуру не только полезной, но и приятной.",
                composition="Aqua, Prunus Amygdalus Dulcis (Sweet Almond) Oil, Emulsifying Wax, Glycerin, Stearic acid, Сaprylic/Capric Triglycerides, Cacao granules, Laminaria Saccharina Extract, Kaolin, Coffea arabica L. (green coffee) seed oil, Methylisothiazolinone, Silica, Parfume, Tocopheryl Acetate, Disodium EDTA.",
                usage="Нанесите скраб на слегка увлажненную кожу, помассируйте в течение 2-3 минут. Смойте остатки теплой водой.",
                image="bioderma_hands.jpg",
                images_list='["bioderma_hands_2.jpg", "bioderma_hands_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Гель для душа увлажняющий",
                brand="SHISEIDO",
                price=1890,
                category="Тело",
                description="Парфюмированный гель для душа из банной линии Ginza, превращаясь в пену при контакте с водой, очищает кожу и придает ей интенсивный аромат с цветочно-древесными нотами. Созданная Карин Дюбрей и Майей Лерну из японского парфюмерного Дома Tagasako, композиция Ginza гармонично сочетает в себе традиции японской парфюмерии и истинно современное прочтение.",
                composition="Используйте парфюмированный гель для душа ежедневно. Сочетайте гель для душа с парфюмерной водой Ginza для усиления и продления стойкости аромата на коже.",
                usage="Нанесите на влажную кожу, вспеньте. Смойте водой. Подходит для ежедневного использования.",
                image="shiseido_shower.jpg",
                images_list='["shiseido_shower_2.jpg"]',
                in_stock=True
            ),
            
            # === Макияж ===
            Product(
                name="Восстанавливающая пудра рассыпчатая",
                brand="STELLARY",
                price=686,
                old_price=890,
                category="Макияж",
                description="Рассыпчатая матирующая пудра PERFECT MATTE FIXING POWDER от STELLARY фиксирует макияж и продлевает его стойкость, блюрит кожу, не меняя ее цвет, и скрывает несовершенства.",
                composition="Synthetic Fluorphlogopite, Silica, Oryza Sativa Starch, Polymethyl Methacrylate, Triethoxycaprylylsilane, Dimethicone, Phenoxyethanol, Caprylyl Glycol, +/-: CI 77491, CI 77492",
                usage="Используйте для фиксации макияжа поверх тонального средства. С помощью пуховки или кисти для пудры STELLARY №141 PRO круговыми полирующими движениями нанесите тонкий слой продукта на всю поверхность лица, уделяя особое внимание Т-зоне.",
                image="stellary_powder.jpg",
                images_list='["stellary_powder_2.jpg", "stellary_powder_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Тональный крем увлажняющий",
                brand="D'ALBA",
                price=2450,
                category="Макияж",
                description="Тональная основа с высоким содержанием увлажняющих компонентов станет настоящим спасением для сухой кожи. Продукт содержит 60% увлажняющей эссенции, благодаря чему тон ложится ровно и естественно, не подчёркивая шелушения. Комплекс натуральных масел и гидролизованная гиалуроновая кислота предотвращают потерю влаги и обеспечивают комфортное ощущение на весь день. Тональная основа ложится лёгким, невесомым слоем и имеет сияющий финиш.",
                composition="Water, Titanium Dioxide(CI 77891), Cyclopentasiloxane, Homosalate, Diphenylsiloxy Phenyl Trimethicone, Methyl Trimethicone, Ethylhexyl Salicylate, Propanediol, Lauryl PEG-10 Tris(Trimethylsiloxy)silylethyl Dimethicone, Niacinamide, 1,2-Hexanediol, Cetyl PEG/PPG-10/1 Dimethicone, Dimethicone, Trimethylsiloxysilicate, Butyrospermum Parkii (Shea) Butter, Limnanthes Alba (Meadowfoam) Seed Oil, Hydrogenated Vegetable Oil, Camellia Japonica Seed Oil, Helianthus Annuus (Sunflower) Seed Oil, Macadamia Integrifolia Seed Oil, Oenothera Biennis (Evening Primrose) Oil, Olea Europaea (Olive) Fruit Oil, Persea Gratissima (Avocado) Oil, Glycine Soja (Soybean) Oil, Caesalpinia Spinosa Fruit Extract, Kappaphycus Alvarezii Extract, Hippophae Rhamnoides Fruit Oil, Centella Asiatica Extract, Tuber Magnatum Extract, Hyaluronic Acid, Nigella Sativa Seed Oil, Hydrolyzed Hyaluronic Acid, Sodium Hyaluronate, Polyphenylsilsesquioxane, Magnesium Sulfate, Disteardimonium Hectorite, Isododecane, Octyldodecanol, Synthetic Fluorphlogopite, Caprylic/Capric Triglyceride, Stearic Acid, Ethylhexyl Hydroxystearate, Alumina, Glycerin, Aluminum Hydroxide, Triethoxycaprylylsilane, Dimethicone/Vinyl Dimethicone Crosspolymer, Polyglyceryl-4 Isostearate, Polyglyceryl-10 Oleate, Polyglyceryl-5 Oleate, Adenosine, Trisodium Ethylenediamine Disuccinate, Isopropyl Titanium Triisostearate, Sodium Stearoyl Glutamate, Tocopherol, Hydroxypropyltrimonium Hyaluronate, Butylene Glycol, Pentaerythrityl Tetra-di-t-butyl Hydroxyhydrocinnamate, Ethylhexylglycerin, Cetearyl Alcohol, Fragrance(Parfum), Limonene, Linalool, Hexyl Cinnamal, Iron Oxides (CI 77492), Bismuth Oxychloride(CI 77163), Mica(CI 77019), Iron Oxides(CI 77491), Iron Oxides(CI 77499)",
                usage="С помощью любого удобного вам аппликатора нанесите небольшое количество средства легкими разглаживающими движениями от центра лица к контурам. Равномерно распределите тон по коже.",
                image="dalba_foundation.jpg",
                images_list='["dalba_foundation_2.jpg", "dalba_foundation_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Помада матовая жидкая",
                brand="STELLARY",
                price=590,
                old_price=750,
                category="Макияж",
                description="С ней вы создадите тот самый трендовый образ с объемными бархатными губами. Кремовая текстура отлично наносится мягким фетровым аппликатором, добавляя макияжу роскоши и эффектности. Помада дарит долгий матовый финиш без сухости, быстро фиксируется и придает губам насыщенный цвет с первого слоя.",
                composition="ISODODECANE, TRIMETHYLSILOXYSILICATE, POLYBUTENE, DIMETHICONE, ISOCETYL STEARATE, ISOHEXADECANE, KAOLIN, DISTEARDIMONIUM HECTORITE, SYNTHETIC BEESWAX, GLYCERYL BEHENATE, SILICA DIMETHYL SILYLATE, PROPYLENE CARBONATE, AROMA , PPG-15 STEARYL ETHER, LECITHIN, TOCOPHEROL, ASCORBYL PALMITATE, CITRIC ACID, +/-: CI 15850 (RED 7 LAKE), CI 15850 (RED 6), CI 77891, CI 77491, CI 77492, CI 77499, CI 42090, CI 19140.",
                usage="Наносите пушистым аппликатором на губы. Чтобы добавить объем, сначала выделите контур карандашом, немного выходя за края.",
                image="stellary_lipstick.jpg",
                images_list='["stellary_lipstick_2.jpg", "stellary_lipstick_3.jpg"]',
                in_stock=True
            ),
            Product(
                name="Тушь для объёма ресниц",
                brand="SHISEIDO",
                price=2190,
                category="Макияж",
                description="Яркий интенсивный цвет и регулируемый объем без комочков. Невесомая формула, представленная в четырех ярких выразительных оттенках, содержит уникальный ком-плекс мягкого и жесткого восков, что обеспечивает идеальную текстуру, гибкость и легкое нанесение. Пленкообразующие вещества и полимеры закрепляют высокопигментированную тушь на 24 часа, она не размазывается, не образует комочков и не осыпается.",
                composition="AQUA PARAFFIN SYNTHETIC BEESWAX CI 77289 PALMITIC ACID STEARIC ACID CI 77288 ACACIA SENEGAL GUM AMINOMETHYL PROPANEDIOL BUTYLENE GLYCOL CI 42090 COPERNICIA CERIFERA CERA GLYCERYLSTEARATE CI 77499 PHENOXYETHANOL VP/EICOSENE COPOLYMER ETHYLHEXYLGLYCERIN POLYGLYCERYL-2 ISOSTEARATE/DIMER DILINOLEATE COPOLYMER SIMMONDSIA CHINENSIS (JOJOBA) SEED OIL HYDROXYETHYLCELLULOSE CI 77491 CI 77492",
                usage="Нанесите на ресницы от корней к кончикам. При необходимости нанесите второй слой.",
                image="shiseido_mascara.jpg",
                images_list='["shiseido_mascara_2.jpg"]',
                in_stock=True
            ),
            Product(
                name="Блеск для губ увлажняющий",
                brand="STELLARY",
                price=490,
                category="Макияж",
                description="BIG LIPS от STELLARY — блески, вдохновленные современным трендом на чувственные, сочные губы. Это инструмент для совершенного образа, который будет привлекать внимание и вызывать восхищение.",
                composition="POLYBUTENE, OCTYLDODECANOL, HYDROGENATED POLYISOBUTENE, SILICA DIMETHYL SILYLATE, TRIMETHYLOLPROPANE TRIISOSTEARATE, VP/HEXADECENE POLYMER, AROMA, RICINUS COMMUNIS (CASTOR) SEED OIL, SODIUM HYALURONATE, POLYGLYCERYL-3 DIISOSTEARATE, HYDROGENATED CASTOR OIL, BENZYL BENZOATE, BENZYL ALCOHOL, LINALOOL, CI 77891, CI 77491, CI 77492, CI 77499, CI 15850 (RED 6), CI 15850 (RED 7 LAKE), CI 42090, CI 19140, CI 45410, CI 77120.",
                usage="Наносите блеск как самостоятельный продукт или в паре с помадой и карандашом для губ от STELLARY, чтобы получить великолепное глянцевое покрытие.",
                image="stellary_gloss.jpg",
                images_list='["stellary_gloss_2.jpg", "stellary_gloss_3.jpg"]',
                in_stock=True
            )
        ]
        
        try:
            db.session.add_all(products)
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', email='admin@beautyforyou.local',
                            password=generate_password_hash('admin123'), is_admin=True)
                db.session.add(admin)
                print("✅ Админ: admin / admin123")
            db.session.commit()
            print(f"✅ Добавлено {len(products)} товаров")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            db.session.rollback()

# ==================== ГЛАВНАЯ СТРАНИЦА ====================
@app.route('/')
def index():
    products = Product.query.filter_by(in_stock=True).limit(4).all()
    return render_template('index.html', products=products)

# ==================== КАТАЛОГ ====================
@app.route('/catalog')
def catalog():
    return render_template('catalog.html')

@app.route('/catalog/<category_name>')
def catalog_category(category_name):
    category_map = {
        'lico': 'Лицо', 'volosy': 'Волосы', 'telo': 'Тело',
        'makiyazh': 'Макияж', 'nabory': 'Наборы'
    }
    
    category = category_map.get(category_name, category_name)
    sort = request.args.get('sort', 'default')
    brand = request.args.get('brand', 'all')
    
    products = Product.query.filter_by(category=category, in_stock=True).all()
    
    if brand != 'all':
        products = [p for p in products if p.brand == brand]
    
    if sort == 'price-asc':
        products.sort(key=lambda x: x.price)
    elif sort == 'price-desc':
        products.sort(key=lambda x: x.price, reverse=True)
    elif sort == 'brand':
        products.sort(key=lambda x: x.brand or '')
    
    if current_user.is_authenticated:
        user_cart = {i.product_id: i.quantity for i in CartItem.query.filter_by(user_id=current_user.id).all()}
    else:
        user_cart = session.get('cart', {})
        user_cart = {int(k): v for k, v in user_cart.items()}
    
    for p in products:
        p.in_cart_qty = user_cart.get(p.id, 0)
    
    brands = sorted(set(p.brand for p in Product.query.filter_by(category=category).all() if p.brand))
    
    category_titles = {
        'Лицо': 'Уход за лицом', 'Волосы': 'Уход за волосами',
        'Тело': 'Уход за телом', 'Макияж': 'Макияж', 'Наборы': 'Наборы'
    }
    
    return render_template('category.html', 
                         products=products, 
                         category=category,
                         category_title=category_titles.get(category, category),
                         brands=brands,
                         current_brand=brand,
                         current_sort=sort)

# ==================== СТРАНИЦА ТОВАРА ====================
@app.route('/product/<int:product_id>')
def product(product_id):
    prod = Product.query.get_or_404(product_id)
    recommended_products = Product.query.filter_by(in_stock=True).limit(8).all()
    return render_template('product.html', product=prod, recommended_products=recommended_products)

@app.route('/about')
def about():
    return render_template('about.html')

# ==================== КОНТАКТЫ ====================
@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not name or not contact or not message:
            return jsonify({'success': False, 'error': 'Заполните все обязательные поля'}), 400
        
        new_message = ContactMessage(
            name=name, contact=contact, subject=subject, message=message
        )
        
        try:
            db.session.add(new_message)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Ошибка сохранения'}), 500
    
    return render_template('contacts.html')

# ==================== АВТОРИЗАЦИЯ ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email_or_username = request.form.get('email', '').strip()
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        user = User.query.filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            flash(f'✓ Добро пожаловать, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('❌ Неверный логин или пароль', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        agree = request.form.get('agree')
        
        if not phone:
            flash('❌ Номер телефона обязателен', 'error')
            return render_template('register.html')
        
        if not agree:
            flash('❌ Необходимо согласиться с условиями', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('❌ Пароли не совпадают', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('❌ Пароль должен быть минимум 6 символов', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('❌ Email уже зарегистрирован', 'error')
            return render_template('register.html')
        
        try:
            user = User(
                username=username, email=email, phone=phone,
                password=generate_password_hash(password), is_admin=False
            )
            db.session.add(user)
            db.session.commit()
            flash('✓ Регистрация успешна! Теперь войдите в аккаунт', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('❌ Ошибка регистрации: ' + str(e), 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('✓ Вы вышли из аккаунта', 'info')
    return redirect(url_for('index'))

# ==================== КОРЗИНА ====================
@app.route('/cart')
def cart():
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
    else:
        cart = session.get('cart', {})
        cart_items = []
        subtotal = 0
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            if product:
                cart_items.append({'product': product, 'quantity': quantity, 'product_id': int(product_id)})
                subtotal += product.price * quantity
    
    recommended_products = Product.query.filter_by(in_stock=True).limit(8).all()
    discount = 0
    total = subtotal - discount
    
    return render_template('cart.html', 
                         cart_items=cart_items, subtotal=subtotal,
                         discount=discount, total=total,
                         recommended_products=recommended_products)

# ==================== ОФОРМЛЕНИЕ ЗАКАЗА ====================
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Получаем товары корзины
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
    else:
        cart = session.get('cart', {})
        cart_items = []
        subtotal = 0
        for pid, qty in cart.items():
            p = Product.query.get(int(pid))
            if p:
                cart_items.append({'product': p, 'quantity': qty})
                subtotal += p.price * qty
    
    if not cart_items:
        flash('Корзина пуста', 'error')
        return redirect(url_for('cart'))
    
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        customer_phone = request.form.get('customer_phone')
        customer_email = request.form.get('customer_email')
        delivery_address = request.form.get('delivery_address')
        delivery_method = request.form.get('delivery_method', 'courier')
        payment_method = request.form.get('payment_method', 'cash')
        comment = request.form.get('comment', '')
        
        if not customer_name or not customer_phone or not delivery_address:
            flash('❌ Заполните все обязательные поля', 'error')
            return redirect(url_for('checkout'))
        
        # ← ← ← ИСПРАВЛЕНИЕ: Правильный доступ к данным корзины
        items_data = []
        for item in cart_items:
            if isinstance(item, dict):
                # Для неавторизованных пользователей (сессия)
                items_data.append({
                    'name': item['product'].name,
                    'price': item['product'].price,
                    'quantity': item['quantity']
                })
            else:
                # Для авторизованных пользователей (CartItem объект)
                items_data.append({
                    'name': item.product.name,
                    'price': item.product.price,
                    'quantity': item.quantity
                })
        
        new_order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            delivery_address=delivery_address,
            delivery_method=delivery_method,
            payment_method=payment_method,
            total_amount=subtotal,
            items_json=json.dumps(items_data),
            comment=comment
        )
        
        try:
            db.session.add(new_order)
            
            if current_user.is_authenticated:
                CartItem.query.filter_by(user_id=current_user.id).delete()
            else:
                session['cart'] = {}
            
            db.session.commit()
            flash('✅ Заказ успешно оформлен!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Ошибка оформления заказа: {str(e)}', 'error')
            return redirect(url_for('checkout'))
    
    return render_template('checkout.html', cart_items=cart_items, total=subtotal)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
            db.session.add(cart_item)
        db.session.commit()
        cart_total = current_user.get_cart_total()
        return jsonify({'success': True, 'cart_total': cart_total})  # ← Добавлен return
    else:
        cart = session.get('cart', {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        session['cart'] = cart
        cart_total = sum(int(v) for v in cart.values())
        return jsonify({'success': True, 'cart_total': cart_total})  # ← Добавлен cart_total

@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id')
    action = request.form.get('action')
    
    if not product_id:
        return jsonify({'success': False, 'error': 'No product_id'}), 400
    
    if current_user.is_authenticated:
        item = CartItem.query.filter_by(user_id=current_user.id, product_id=int(product_id)).first()
        if item:
            if action == 'increase':
                item.quantity += 1
            elif action == 'decrease':
                item.quantity -= 1
                if item.quantity <= 0:
                    db.session.delete(item)
            db.session.commit()
            total = current_user.get_cart_total()
        else:
            total = 0
    else:
        cart = session.get('cart', {})
        if str(product_id) in cart:
            if action == 'increase':
                cart[str(product_id)] += 1
            elif action == 'decrease':
                cart[str(product_id)] -= 1
                if cart[str(product_id)] <= 0:
                    del cart[str(product_id)]
            session['cart'] = cart
        total = sum(int(v) for v in cart.values())
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_total': total})
    
    return redirect(url_for('cart'))

# ← Исправлено маршрут
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if current_user.is_authenticated:
        item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
        total = current_user.get_cart_total()
    else:
        cart = session.get('cart', {})
        if str(product_id) in cart:
            del cart[str(product_id)]
            session['cart'] = cart
        total = sum(int(v) for v in cart.values())
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_total': total})
    
    flash('✓ Товар удалён из корзины', 'success')
    return redirect(url_for('cart'))

@app.route('/api/cart_count')
def api_cart_count():
    if current_user.is_authenticated:
        count = current_user.get_cart_total()
    else:
        cart = session.get('cart', {})
        count = sum(int(v) for v in cart.values())
    return jsonify({'count': count or 0})

# ==================== АДМИН-ПАНЕЛЬ ====================
# ← Исправлено: добавлен # перед заголовком
# === АДМИН-ПАНЕЛЬ ===

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    
    total_products = Product.query.count()
    total_users = User.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(Order.status != 'cancelled').scalar() or 0
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    low_stock = Product.query.filter_by(in_stock=True).limit(5).all()
    
    return render_template('admin/index.html',
                         total_products=total_products, total_users=total_users,
                         total_orders=total_orders, total_revenue=total_revenue,
                         recent_orders=recent_orders, low_stock=low_stock)

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def admin_product_add():
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            product = Product(
                name=request.form.get('name'), brand=request.form.get('brand'),
                category=request.form.get('category'), price=float(request.form.get('price')),
                old_price=float(request.form.get('old_price')) if request.form.get('old_price') else None,
                image=request.form.get('image'), description=request.form.get('description', ''),
                composition=request.form.get('composition', ''), usage=request.form.get('usage', ''),
                in_stock=request.form.get('in_stock') == 'on'
            )
            db.session.add(product)
            db.session.commit()
            flash('✅ Товар добавлен', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Ошибка: {e}', 'error')
    return render_template('admin/product_form.html', product=None)

# ← Исправлено маршрут
@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_product_edit(product_id):
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.brand = request.form.get('brand')
            product.category = request.form.get('category')
            product.price = float(request.form.get('price'))
            product.old_price = float(request.form.get('old_price')) if request.form.get('old_price') else None
            product.image = request.form.get('image')
            product.description = request.form.get('description', '')
            product.composition = request.form.get('composition', '')
            product.usage = request.form.get('usage', '')
            product.in_stock = request.form.get('in_stock') == 'on'
            db.session.commit()
            flash('✅ Товар обновлён', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Ошибка: {e}', 'error')
    return render_template('admin/product_form.html', product=product)

# ← Исправлено маршрут
@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
def admin_product_delete(product_id):
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('✅ Товар удалён', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

# ← Исправлено маршрут
@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def admin_order_status(order_id):
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status')
    db.session.commit()
    flash('✅ Статус обновлён', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/messages')
@login_required
def admin_messages():
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)

# ← Исправлено маршрут
@app.route('/admin/message/<int:id>/read', methods=['POST'])
@login_required
def mark_message_read(id):
    if not current_user.is_admin:
        flash('❌ Доступ запрещён', 'error')
        return redirect(url_for('index'))
    message = ContactMessage.query.get_or_404(id)
    message.is_read = True
    db.session.commit()
    flash('✅ Сообщение отмечено', 'success')
    return redirect(url_for('admin_messages'))

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def _get_cart():
    if current_user.is_authenticated:
        return {str(i.product_id): i.quantity for i in CartItem.query.filter_by(user_id=current_user.id).all()}
    return session.get('cart', {})

def _calc_cart(cart):
    items, total = [], 0
    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if p:
            items.append({'product': p, 'quantity': qty})
            total += p.price * qty
    return items, total

def _update_cart(product_id, delta):
    if current_user.is_authenticated:
        item = CartItem.query.filter_by(user_id=current_user.id, product_id=int(product_id)).first()
        if item:
            item.quantity += delta
            if item.quantity <= 0:
                db.session.delete(item)
        elif delta > 0:
            db.session.add(CartItem(user_id=current_user.id, product_id=int(product_id), quantity=1))
        db.session.commit()
    else:
        cart = session.get('cart', {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + delta
        if cart[str(product_id)] <= 0:
            del cart[str(product_id)]
        session['cart'] = cart

def _remove_cart(product_id):
    if current_user.is_authenticated:
        item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
    else:
        cart = session.get('cart', {})
        cart.pop(str(product_id), None)
        session['cart'] = cart

def _clear_cart():
    if current_user.is_authenticated:
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
    else:
        session['cart'] = {}

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    with app.app_context():
        try: init_db()
        except Exception as e: print(f"⚠️ Ошибка БД: {e}")
    app.run(debug=True, port=5000)
    