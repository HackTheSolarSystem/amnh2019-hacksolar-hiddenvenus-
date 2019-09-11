◊(local-require txexpr)
◊(define (rel-root path) (string-append "/amnh2019-hacksolar-hiddenvenus-" path))
<html>
    <head>
        <script>
        MathJax = {
        tex: {
            inlineMath: [['$', '$'], ['\\(', '\\)']]
        }
        };
        </script>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    ◊(->html (meta #:charset "UTF-8"))
    ◊(->html (link #:rel "stylesheet" #:type "text/css" 
                   #:href ◊(rel-root "/docs/style.css")))
    </head>
    ◊(->html
            `(body 
                (nav ((id "site-nav"))
                 (a ((href ,◊rel-root{/index.html})) "Index") 
                 (span ((class "nav-spacer")) "|" )
                 (a ((href ,◊rel-root{/docs/intro.html})) 
                    "Introduction to Project")
                 (span ((class "nav-spacer")) "|" )
                 (a ((href ,◊rel-root{/docs/details/satellite.html})) 
                    "How Magellan Orbited Venus"))
                ,@(get-elements doc)))
</html>
