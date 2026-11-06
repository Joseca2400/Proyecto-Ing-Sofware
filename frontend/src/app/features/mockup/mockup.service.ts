import { Injectable, signal } from '@angular/core';

export interface UnidadDemo {
  codigo: string;
  modelo: string;
  tipo: string;
  anio: string;
  vin: string;
  placa: string;
  estado: string;
  tono: string;
  kilometraje: string;
  costo: string;
  compra: string;
  importacion: string;
  taller: string;
  ingreso: string;
  resultado: string;
  ocupacion: string;
}

export interface ContratoDemo {
  numero: string;
  cliente: string;
  unidad: string;
  salida: string;
  devolucion: string;
  estado: string;
  tarifa: string;
  moneda: 'GTQ' | 'USD';
  deposito: string;
  kilometraje: string;
  combustible: string;
}

@Injectable({ providedIn: 'root' })
export class MockupService {
  // Escenario ilustrativo. Los importes son texto; no se calculan ni convierten en el navegador.
  readonly unidades: UnidadDemo[] = [
    {
      codigo: 'KC-001',
      modelo: 'Toyota RAV4',
      tipo: 'SUV',
      anio: '2022',
      vin: '2T3W1RFV2NW183201',
      placa: 'P-482 KLM',
      estado: 'Alquilada',
      tono: 'azul',
      kilometraje: '42,850',
      costo: '128500.00',
      compra: '100000.00',
      importacion: '23000.00',
      taller: '5500.00',
      ingreso: '12600.00',
      resultado: '7800.00',
      ocupacion: '87',
    },
    {
      codigo: 'KC-002',
      modelo: 'Hyundai Tucson',
      tipo: 'SUV',
      anio: '2021',
      vin: 'KM8J3CA46MU317204',
      placa: 'P-716 JTR',
      estado: 'Disponible',
      tono: 'verde',
      kilometraje: '36,200',
      costo: '112800.00',
      compra: '90000.00',
      importacion: '19000.00',
      taller: '3800.00',
      ingreso: '10800.00',
      resultado: '6450.00',
      ocupacion: '80',
    },
    {
      codigo: 'KC-003',
      modelo: 'Toyota Corolla',
      tipo: 'Sedán',
      anio: '2022',
      vin: 'JTDEPMAE5NJ218603',
      placa: 'P-309 KNS',
      estado: 'Alquilada',
      tono: 'azul',
      kilometraje: '28,410',
      costo: '96700.00',
      compra: '78000.00',
      importacion: '16000.00',
      taller: '2700.00',
      ingreso: '8400.00',
      resultado: '5100.00',
      ocupacion: '90',
    },
    {
      codigo: 'KC-004',
      modelo: 'Kia Sportage',
      tipo: 'SUV',
      anio: '2020',
      vin: 'KNDPMCAC5L7819604',
      placa: 'P-625 HFP',
      estado: 'En taller',
      tono: 'ambar',
      kilometraje: '58,900',
      costo: '104500.00',
      compra: '82000.00',
      importacion: '18000.00',
      taller: '4500.00',
      ingreso: '6300.00',
      resultado: '2800.00',
      ocupacion: '63',
    },
    {
      codigo: 'KC-005',
      modelo: 'Honda CR-V',
      tipo: 'SUV',
      anio: '2023',
      vin: '2HKRS4H52PH102805',
      placa: 'Pendiente',
      estado: 'En tránsito',
      tono: 'gris',
      kilometraje: '18,600',
      costo: '107800.00',
      compra: '107800.00',
      importacion: '0.00',
      taller: '0.00',
      ingreso: '0.00',
      resultado: '0.00',
      ocupacion: '0',
    },
    {
      codigo: 'KC-006',
      modelo: 'Mazda CX-5',
      tipo: 'SUV',
      anio: '2021',
      vin: 'JM3KFBCM1M0418206',
      placa: 'P-853 JWX',
      estado: 'Disponible',
      tono: 'verde',
      kilometraje: '39,120',
      costo: '119600.00',
      compra: '95000.00',
      importacion: '20000.00',
      taller: '4600.00',
      ingreso: '11400.00',
      resultado: '6900.00',
      ocupacion: '83',
    },
  ];
  readonly contratos = signal<ContratoDemo[]>([
    {
      numero: 'ALQ-2026-048',
      cliente: 'Ana Lucía Méndez',
      unidad: 'KC-001',
      salida: '2026-11-02T09:00',
      devolucion: '2026-11-08T09:00',
      estado: 'Activo',
      tarifa: '450.00',
      moneda: 'GTQ',
      deposito: '1500.00',
      kilometraje: '42850',
      combustible: 'Lleno',
    },
    {
      numero: 'ALQ-2026-049',
      cliente: 'Logística del Valle',
      unidad: 'KC-003',
      salida: '2026-11-04T10:00',
      devolucion: '2026-11-11T10:00',
      estado: 'Activo',
      tarifa: '350.00',
      moneda: 'GTQ',
      deposito: '1200.00',
      kilometraje: '28410',
      combustible: 'Lleno',
    },
  ]);
  readonly facturas = [
    {
      numero: 'FEL-2026-0182',
      cliente: 'Logística del Valle',
      concepto: 'Alquiler · KC-003',
      vence: '05 nov 2026',
      monto: '8400.00',
      moneda: 'GTQ' as const,
      estado: 'Vencida',
      tono: 'rojo',
    },
    {
      numero: 'FEL-2026-0183',
      cliente: 'Ana Lucía Méndez',
      concepto: 'Alquiler · KC-001',
      vence: '08 nov 2026',
      monto: '2700.00',
      moneda: 'GTQ' as const,
      estado: 'Por cobrar',
      tono: 'ambar',
    },
    {
      numero: 'FEL-2026-0184',
      cliente: 'Viajes Altiplano',
      concepto: 'Alquiler · KC-006',
      vence: '10 nov 2026',
      monto: '650.00',
      moneda: 'USD' as const,
      estado: 'Por cobrar',
      tono: 'ambar',
    },
  ];
  readonly partidas = [
    {
      numero: 'PAR-00128',
      concepto: 'Compra de Honda CR-V · KC-005',
      origen: 'Compras',
      debe: '107800.00',
      haber: '107800.00',
      estado: 'Por revisar',
      tono: 'ambar',
    },
    {
      numero: 'PAR-00127',
      concepto: 'Factura de alquiler · KC-003',
      origen: 'Facturación',
      debe: '8400.00',
      haber: '8400.00',
      estado: 'Contabilizada',
      tono: 'verde',
    },
    {
      numero: 'PAR-00126',
      concepto: 'Mano de obra · OT-026',
      origen: 'Taller',
      debe: '1800.00',
      haber: '1800.00',
      estado: 'Contabilizada',
      tono: 'verde',
    },
  ];

  guardarBorrador(datos: Omit<ContratoDemo, 'numero' | 'estado'>): void {
    this.contratos.update((contratos) => [
      { ...datos, numero: `BORRADOR-${contratos.length - 1}`, estado: 'Borrador demo' },
      ...contratos,
    ]);
  }
}
