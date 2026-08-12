from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date, Time
from sqlalchemy.orm import declarative_base, relationship
from datetime import date, datetime

Base = declarative_base()


class Terminal(Base):
    """Maneja las cajas físicas o puntos de cobro del negocio."""
    __tablename__ = 'terminales'

    id_terminal = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)  # Ej: "Caja Principal", "Caja 2"
    activa = Column(Boolean, default=True)

    # Relación: Un terminal puede tener muchas ventas
    ventas = relationship("Venta", back_populates="terminal")


class Producto(Base):
    """Equivale a la hoja 'Inventario' del prototipo."""
    __tablename__ = 'productos'

    id_producto = Column(Integer, primary_key=True, autoincrement=True)
    codigo_qr = Column(String(100), unique=True, nullable=True)
    sku = Column(String(50), unique=True, nullable=False)
    nombre_producto = Column(String(150), nullable=False)
    categoria = Column(String(50))
    
    # Unidad de Medida (UN, KG, LT, etc.)
    unidad_medida = Column(String(20), default="UN", nullable=False)

    # Valores económicos
    costo_compra_neto = Column(Float, nullable=False, default=0.0)
    precio_venta_base = Column(Float, nullable=False)
    descuento_producto = Column(Float, default=0.0)
    valor_final = Column(Float, nullable=False)

    # Control de Stock (Float para permitir kilos/fraccionados)
    stock_actual = Column(Float, default=0.0)
    stock_minimo = Column(Float, default=0.0)
    estado_producto = Column(String(20), default="Activo")  # "Activo", "Inactivo"
    fecha_ultima_compra = Column(Date, default=date.today)

    # Relación
    items_vendidos = relationship("VentaItem", back_populates="producto")


class Venta(Base):
    """Equivale a 'IngresoVentas', funciona como la cabecera de la transacción."""
    __tablename__ = 'ventas'

    id_venta = Column(Integer, primary_key=True, autoincrement=True)
    id_terminal = Column(Integer, ForeignKey('terminales.id_terminal'), nullable=False)

    fecha = Column(Date, default=date.today)
    hora = Column(Time, default=lambda: datetime.now().time())
    turno = Column(String(20))

    # Totales calculados
    total_valor_final = Column(Float, default=0.0)
    descuento_general = Column(Float, default=0.0)
    total_monto = Column(Float, default=0.0)

    # Relaciones
    terminal = relationship("Terminal", back_populates="ventas")
    items = relationship("VentaItem", back_populates="venta", cascade="all, delete-orphan")
    cierre_caja = relationship("Caja", back_populates="venta", uselist=False)


class VentaItem(Base):
    """Detalle de los productos vendidos. Clave para las métricas de 'productos más vendidos'."""
    __tablename__ = 'venta_items'

    id_item = Column(Integer, primary_key=True, autoincrement=True)
    id_venta = Column(Integer, ForeignKey('ventas.id_venta'), nullable=False)
    id_producto = Column(Integer, ForeignKey('productos.id_producto'), nullable=False)

    # Float para soportar decimales en venta por Kilo
    cantidad = Column(Float, nullable=False)
    precio_base = Column(Float, nullable=False)
    valor_final = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relaciones
    venta = relationship("Venta", back_populates="items")
    producto = relationship("Producto", back_populates="items_vendidos")


class Caja(Base):
    """Equivale a la hoja 'Caja'. Representa el cierre financiero real."""
    __tablename__ = 'caja'

    id_caja = Column(Integer, primary_key=True, autoincrement=True)
    id_venta = Column(Integer, ForeignKey('ventas.id_venta'), nullable=False, unique=True)

    total_monto = Column(Float, nullable=False)
    descuento_final = Column(Float, default=0.0)
    total_pagar = Column(Float, nullable=False)
    medio_pago = Column(String(50), nullable=False)  # Ej: Transferencia, Débito, Crédito, Efectivo

    impuesto_monto = Column(Float, default=0.0)
    monto_venta = Column(Float, nullable=False)
    descuentos_totales = Column(Float, default=0.0)

    # Relación
    venta = relationship("Venta", back_populates="cierre_caja")