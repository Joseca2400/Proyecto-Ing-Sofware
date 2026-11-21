import { Component, computed, inject, signal } from '@angular/core';
import {
  ActivatedRoute,
  NavigationEnd,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';
import {
  LucideArrowLeftRight,
  LucideBanknote,
  LucideBookMarked,
  LucideBookOpen,
  LucideBuilding2,
  LucideCalendarCheck,
  LucideCalendarClock,
  LucideCar,
  LucideCarFront,
  LucideChartColumn,
  LucideChartPie,
  LucideClock,
  LucideDollarSign,
  LucideDynamicIcon,
  LucideFileSignature,
  LucideFileSpreadsheet,
  LucideFileText,
  LucideHistory,
  LucideHourglass,
  LucideIcon,
  LucideIdCard,
  LucideLandmark,
  LucideLayoutDashboard,
  LucideListChecks,
  LucideListTree,
  LucideLogOut,
  LucideMenu,
  LucideMoon,
  LucidePalette,
  LucideReceipt,
  LucideRoute,
  LucideScale,
  LucideShieldCheck,
  LucideShip,
  LucideShoppingCart,
  LucideSun,
  LucideTag,
  LucideTrendingDown,
  LucideTrendingUp,
  LucideUserCog,
  LucideUsers,
  LucideWrench,
  LucideX,
} from '@lucide/angular';
import { AuthService, NOMBRE_ROL } from '../auth/auth.service';
import { TemaService } from '../tema/tema.service';

interface EntradaMenu {
  etiqueta: string;
  ruta: string;
  icono: LucideIcon;
}

interface SeccionMenu {
  titulo?: string;
  entradas: EntradaMenu[];
}

@Component({
  selector: 'app-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, LucideDynamicIcon],
  templateUrl: './layout.html',
  styleUrl: './layout.css',
})
export class Layout {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  // Los roles de cada pantalla se declaran una sola vez, en `data` de su ruta (app.routes.ts).
  private readonly rolesPorRuta = new Map<string, string[] | undefined>(
    (inject(ActivatedRoute).routeConfig?.children ?? []).map((hija) => [
      `/${hija.path}`,
      hija.data?.['roles'],
    ]),
  );

  protected readonly iconos = {
    salir: LucideLogOut,
    abrir: LucideMenu,
    cerrar: LucideX,
    sol: LucideSun,
    luna: LucideMoon,
  };
  protected readonly tema = inject(TemaService);
  protected readonly oscuro = computed(() => this.tema.tema() === 'oscuro');
  protected readonly usuario = this.auth.usuario;
  protected readonly rol = computed(() => NOMBRE_ROL[this.usuario()?.rol ?? ''] ?? '');
  protected readonly iniciales = computed(() =>
    (this.usuario()?.nombre ?? '')
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((parte) => parte[0].toUpperCase())
      .join(''),
  );
  /** En pantallas angostas el menú es un panel que se abre con el botón de la barra. */
  protected readonly menuAbierto = signal(false);

  // Solo las entradas que el rol puede abrir; una sección sin entradas visibles no se muestra.
  protected readonly menu = computed<SeccionMenu[]>(() =>
    this.secciones
      .map((seccion) => ({
        ...seccion,
        entradas: seccion.entradas.filter((entrada) =>
          this.auth.tieneRol(this.rolesPorRuta.get(entrada.ruta)),
        ),
      }))
      .filter((seccion) => seccion.entradas.length > 0),
  );

  // Las secciones siguen el recorrido de la unidad.
  private readonly secciones: SeccionMenu[] = [
    { entradas: [{ etiqueta: 'Inicio', ruta: '/inicio', icono: LucideLayoutDashboard }] },
    {
      titulo: 'Compras e importación',
      entradas: [
        { etiqueta: 'Proveedores', ruta: '/compras/proveedores', icono: LucideBuilding2 },
        {
          etiqueta: 'Compra en EE. UU.',
          ruta: '/compras/compra-unidades',
          icono: LucideShoppingCart,
        },
        {
          etiqueta: 'Gastos de importación',
          ruta: '/compras/gastos-importacion',
          icono: LucideShip,
        },
        { etiqueta: 'Facturas de compras', ruta: '/compras/facturas', icono: LucideReceipt },
        { etiqueta: 'Hoja de costo', ruta: '/compras/hoja-costo', icono: LucideFileSpreadsheet },
        {
          etiqueta: 'Programación de pagos',
          ruta: '/compras/programacion-pagos',
          icono: LucideCalendarClock,
        },
        { etiqueta: 'Pagos a proveedores', ruta: '/compras/pagos', icono: LucideBanknote },
      ],
    },
    {
      titulo: 'Unidades y flota',
      entradas: [
        { etiqueta: 'Unidades', ruta: '/unidades', icono: LucideCar },
        {
          etiqueta: 'Etapas de importación',
          ruta: '/unidades/etapas-importacion',
          icono: LucideRoute,
        },
        { etiqueta: 'Órdenes de taller', ruta: '/taller/ordenes', icono: LucideWrench },
        { etiqueta: 'Tarifas de taller', ruta: '/taller/tarifas', icono: LucideClock },
        { etiqueta: 'Alta en flota', ruta: '/unidades/alta-flota', icono: LucideCarFront },
        { etiqueta: 'Depreciación', ruta: '/unidades/depreciacion', icono: LucideTrendingDown },
        { etiqueta: 'Fin de vida útil', ruta: '/unidades/fin-vida-util', icono: LucideHourglass },
      ],
    },
    {
      titulo: 'Alquiler y facturación',
      entradas: [
        { etiqueta: 'Clientes', ruta: '/facturacion/clientes', icono: LucideUsers },
        { etiqueta: 'Tarifario', ruta: '/alquileres/tarifario', icono: LucideTag },
        { etiqueta: 'Contratos', ruta: '/alquileres/contratos', icono: LucideFileSignature },
        {
          etiqueta: 'Depósitos en garantía',
          ruta: '/alquileres/depositos',
          icono: LucideShieldCheck,
        },
        { etiqueta: 'Facturas', ruta: '/facturacion/facturas', icono: LucideFileText },
      ],
    },
    {
      titulo: 'Contabilidad',
      entradas: [
        { etiqueta: 'Partidas', ruta: '/contabilidad/partidas', icono: LucideBookOpen },
        { etiqueta: 'Balance de comprobación', ruta: '/contabilidad/balance', icono: LucideScale },
        { etiqueta: 'Mayor', ruta: '/contabilidad/mayor', icono: LucideBookMarked },
        { etiqueta: 'Cierre de mes', ruta: '/contabilidad/cierre-mes', icono: LucideCalendarCheck },
        {
          etiqueta: 'Reglas de contabilización',
          ruta: '/contabilidad/reglas',
          icono: LucideListChecks,
        },
        { etiqueta: 'Catálogo de cuentas', ruta: '/configuracion/catalogo', icono: LucideListTree },
      ],
    },
    {
      titulo: 'Reportes',
      entradas: [
        {
          etiqueta: 'Unidades por etapa',
          ruta: '/reportes/unidades-etapa',
          icono: LucideChartColumn,
        },
        { etiqueta: 'Rentabilidad', ruta: '/reportes/rentabilidad', icono: LucideTrendingUp },
        {
          etiqueta: 'Rentabilidad en el ciclo',
          ruta: '/reportes/rentabilidad-ciclo',
          icono: LucideChartPie,
        },
      ],
    },
    {
      titulo: 'Configuración',
      entradas: [
        {
          etiqueta: 'Tipo de cambio',
          ruta: '/configuracion/tipo-cambio',
          icono: LucideArrowLeftRight,
        },
        {
          etiqueta: 'Transacciones USD',
          ruta: '/configuracion/transacciones-usd',
          icono: LucideDollarSign,
        },
        {
          etiqueta: 'Cuentas bancarias',
          ruta: '/configuracion/cuentas-bancarias',
          icono: LucideLandmark,
        },
        { etiqueta: 'Perfil fiscal', ruta: '/configuracion/perfil-fiscal', icono: LucideIdCard },
        { etiqueta: 'Usuarios', ruta: '/seguridad/usuarios', icono: LucideUserCog },
        { etiqueta: 'Bitácora', ruta: '/seguridad/bitacora', icono: LucideHistory },
        { etiqueta: 'Mockup del proyecto', ruta: '/mockup', icono: LucidePalette },
      ],
    },
  ];

  constructor() {
    // Al navegar se cierra el panel del menú en pantallas angostas.
    this.router.events
      .pipe(
        filter((evento) => evento instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.menuAbierto.set(false));
  }

  protected salir(): void {
    this.auth.salir();
    void this.router.navigate(['/entrar']);
  }
}
