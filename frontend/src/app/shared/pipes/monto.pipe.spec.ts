import { MontoPipe } from './monto.pipe';

describe('MontoPipe', () => {
  const pipe = new MontoPipe();

  it('formatea quetzales con dos decimales', () => {
    expect(pipe.transform('1234.5')).toContain('1,234.50');
    expect(pipe.transform('1234.5')).toContain('Q');
  });

  it('formatea dólares', () => {
    expect(pipe.transform('99.999', 'USD')).toContain('100.00');
  });

  it('no pierde precisión con montos grandes', () => {
    expect(pipe.transform('123456789012345.675')).toContain('123,456,789,012,345.68');
  });

  it('devuelve vacío si no hay monto', () => {
    expect(pipe.transform(null)).toBe('');
  });
});
