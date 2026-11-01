// Convierte un HTML de páginas carta (816 × 1056 px, una <section> por página) en PDF con WebKit.
// Uso: swift html_a_pdf.swift entrada.html salida.pdf   (solo macOS)
import AppKit
import WebKit
import PDFKit

let args = CommandLine.arguments
let htmlURL = URL(fileURLWithPath: args[1])
let outURL = URL(fileURLWithPath: args[2])
let W: CGFloat = 816, Hh: CGFloat = 1056

class Del: NSObject, WKNavigationDelegate {
  var web: WKWebView!
  func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
    webView.evaluateJavaScript("document.fonts.ready.then(()=>document.querySelectorAll('section').length)") { _, _ in
      DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
        webView.evaluateJavaScript("[document.querySelectorAll('section').length, document.body.scrollHeight]") { r, _ in
          let a = r as! [Any]
          let n = (a[0] as! NSNumber).intValue
          self.render(n: n, i: 0, doc: PDFDocument())
        }
      }
    }
  }
  func render(n: Int, i: Int, doc: PDFDocument) {
    if i == n { doc.write(to: outURL); print("PDF de \(n) páginas: \(outURL.lastPathComponent)"); exit(0) }
    let cfg = WKPDFConfiguration()
    cfg.rect = CGRect(x: 0, y: CGFloat(i) * Hh, width: W, height: Hh)
    web.createPDF(configuration: cfg) { res in
      if case .success(let data) = res, let p = PDFDocument(data: data)?.page(at: 0) {
        doc.insert(p, at: doc.pageCount)
      } else { print("error pagina", i) }
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
