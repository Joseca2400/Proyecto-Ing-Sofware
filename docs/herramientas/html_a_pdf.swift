// Convierte un HTML de páginas carta (816 × 1056 px, una <section> por página) en PDF con WebKit.
// Uso: swift html_a_pdf.swift entrada.html salida.pdf   (solo macOS)
// Termina con error si una página no se pudo generar o si su contenido invade el pie o se sale de la página.
import AppKit
import WebKit
import PDFKit

let args = CommandLine.arguments
let htmlURL = URL(fileURLWithPath: args[1])
let outURL = URL(fileURLWithPath: args[2])
let W: CGFloat = 816, Hh: CGFloat = 1056

// Devuelve los números de página cuyo contenido baja más allá del pie (o del borde, si no hay pie).
let revisarDesbordes = """
[...document.querySelectorAll('section')].map((s, i) => {
  const pie = s.querySelector('.foot');
  const limite = pie ? pie.getBoundingClientRect().top - 4 : s.getBoundingClientRect().bottom;
  let fondo = 0;
  s.querySelectorAll('*').forEach(e => {
    if (pie && (e === pie || pie.contains(e))) return;
    const r = e.getBoundingClientRect();
    if (r.height > 0) fondo = Math.max(fondo, r.bottom);
  });
  return fondo > limite ? i + 1 : 0;
}).filter(n => n > 0)
"""

class Del: NSObject, WKNavigationDelegate {
  var web: WKWebView!
  var fallas = 0
  var desbordes: [Int] = []
  func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
    webView.evaluateJavaScript("document.fonts.ready.then(()=>document.querySelectorAll('section').length)") { _, _ in
      DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
        webView.evaluateJavaScript(revisarDesbordes) { r, _ in
          self.desbordes = (r as? [NSNumber])?.map { $0.intValue } ?? []
          webView.evaluateJavaScript("document.querySelectorAll('section').length") { r, _ in
            self.render(n: (r as! NSNumber).intValue, i: 0, doc: PDFDocument())
          }
        }
      }
    }
  }
  func render(n: Int, i: Int, doc: PDFDocument) {
    if i == n {
      doc.write(to: outURL)
      print("PDF de \(n) páginas: \(outURL.lastPathComponent)")
      for p in desbordes { print("Aviso: el contenido de la página \(p) invade el pie o se sale de la página") }
      exit(fallas == 0 && desbordes.isEmpty ? 0 : 1)
    }
    let cfg = WKPDFConfiguration()
    cfg.rect = CGRect(x: 0, y: CGFloat(i) * Hh, width: W, height: Hh)
    web.createPDF(configuration: cfg) { res in
      if case .success(let data) = res, let p = PDFDocument(data: data)?.page(at: 0) {
        doc.insert(p, at: doc.pageCount)
      } else { print("Error al generar la página", i + 1); self.fallas += 1 }
      self.render(n: n, i: i + 1, doc: doc)
    }
  }
}
let app = NSApplication.shared
let web = WKWebView(frame: CGRect(x: 0, y: 0, width: W, height: Hh * 40))
let d = Del(); d.web = web; web.navigationDelegate = d
web.loadFileURL(htmlURL, allowingReadAccessTo: htmlURL.deletingLastPathComponent())
DispatchQueue.main.asyncAfter(deadline: .now() + 60) { print("timeout"); exit(1) }
app.run()
