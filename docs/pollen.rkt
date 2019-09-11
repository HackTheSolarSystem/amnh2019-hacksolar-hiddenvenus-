#lang racket

(require pollen-utilities/utility
         pollen/tag
         pollen/core
         pollen/template
         txexpr)
(provide (all-defined-out))

(define (code . elements)
 (apply @ `("`" ,@elements "`")))
(define (image-path path)
  (~a "/readme-images/" path))
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
  (apply @ `("$" ,@elements "$")))
(define (ignore . elements)
  (@ ""))
(define (just-mark . elements)
  (apply @ elements))
(define todo ignore)
; ns: needs source
(define ns just-mark)
(define term em)
(define path code)
