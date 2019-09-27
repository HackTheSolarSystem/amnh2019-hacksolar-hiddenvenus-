#lang racket

(require pollen/tag
         pollen/core
         pollen/template
         pollen/decode
         txexpr
         (only-in markdown parse-markdown))
(provide (all-defined-out))

(define (is-tag? tag . names)
  (and (txexpr? tag) (member (get-tag tag) names)))

(define (rel-root path) (string-append "/amnh2019-hacksolar-hiddenvenus-" path))

(define (code . elements)
 (apply @ `("`" ,@elements "`")))
(define (image-path path)
  (rel-root (~a "/docs/readme-images/" path)))
(define (page-link path . text)
  (if (null? text)
    (format "<~a>" (rel-root path))
    (apply @ `("[" ,@text "](" ,(rel-root path) ")"))))
(define (paper . elements) 
  (cond 
    [(symbol? (first elements))
     (define-values (ref page) 
       (values (first elements) (second elements)))
     (@ (~a "(" ref " page " page ")"))]
    [else (apply path "papers+documents/" elements)]))

(define-tag-function
  (img attrs elements)
  (define path (first elements))
  (define alt-text (rest elements))
  (define full-path (image-path path))
  (@
    (->html 
      `(div 
         ((class "img-container"))
         (img ,(append 
                 attrs 
                 `((src ,full-path) 
                   (alt ,(string-join alt-text "")))))))
    (->html `(p ((class "caption")) ,@alt-text))))

(define (em . elements)
  (apply @ `("*" ,@elements "*")))
(define ($ . elements)
  (apply @ `("\\\\-(" ,@elements "\\\\-)")))
(define (ignore . elements)
  (@ ""))
; These are entirely semantic, but won't get ignored in the output.
(define (just-mark . elements)
  (apply @ elements))
; These are only for the editor to see.
(define (todo . elements)
  (txexpr 'todo null null))
; ns: needs source
(define ns just-mark)
(define term em)
(define path code)

(define (deg . elements)
  (apply @ `(,@elements "\u00b0")))
; Input should be
; stuff " by " stuff
; and will replace the "by" with X
(define by "\u00d7")

(define under-construction
  (->html
    '(div 
       ((class "construction-banner"))
       (span
         #x2622
         (strong "UNDER HEAVY CONSTRUCTION!")
         #x2622)
       (div #x2b07))))
(define coming-soon
  (->html
    '(div 
       ((class "coming-soon-banner"))
       "Coming Soon!")))

(define (root . elements)
  (define (remove-todo elements)
    (define-values (ignore elements-without-todo)
      (for/fold ([state 'start] [so-far null])
        ([current elements])
        (cond
          [(is-tag? current 'todo)
           (values 'found-todo so-far)]
          [(and (eq? state 'found-todo)
                (string=? current "\n"))
           (values 'start so-far)]
          [else (values 'start (append so-far (list current)))])))
    elements-without-todo)
  (define (fix-todo elements)
    (decode-elements 
      elements
      #:txexpr-elements-proc remove-todo))
  (txexpr 'root null 
          (parse-markdown 
            (string-join 
              (fix-todo elements)
              ""))))
  
