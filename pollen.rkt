#lang racket

(require pollen/tag
         pollen/core
         pollen/template
         pollen/decode
         txexpr
         (only-in markdown parse-markdown))
(provide (all-defined-out))

(define is-draft? 
  (and (getenv "POLLEN")
       (string=? (getenv "POLLEN") "draft")))

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
; TODO
; - Change paper to produce paths to papers+documents/
; - Use symbols to point to a particular paper, don't re-type up the
;   path every time.
; - Improve the way that references are shown.
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
; TODO
; - See if you can move the transformation of todos out of the root
;   tag and into here. Figure out how to make sure the splicing tag
;   doesn't get in your way.
(define (todo . elements)
  (if is-draft?
    (txexpr 'todo null elements)
    (txexpr 'todo null null)))
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
; TODO
; - See if there is a way to make draft and doc-draft one element.
; - Alter doc-draft so that the draft styles can be toggled on and
;   off, and the draft section can be shrunk down. Shrunk can show
;   some of the very top, and some big ellipsis in the center.
(define (draft . elements)
  (if is-draft? 
    (apply @ elements)
    (@ "")))
(define (doc-draft . elements)
  (if is-draft? 
    (txexpr 'draft-content null elements)
    (@ "")))

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
  (define (fix-draft-elements elements)
    (if (not is-draft?)
      (decode-elements 
        elements
        #:txexpr-elements-proc remove-todo)
      (decode-elements
        elements
        #:txexpr-proc
        (λ (tx)
           (cond
             [(not (is-tag? tx 'todo 'draft-content)) tx]
             [(is-tag? tx 'todo)
              (->html
                `(div ((class "todo"))
                      "TODO: "
                      ,@(parse-markdown 
                          (string-join (get-elements tx)))))]
             [(is-tag? tx 'draft-content)
              (->html
                `(div ((class "draft"))
                      ,@(parse-markdown 
                          (string-join (get-elements tx)))))])
             ))))
    (txexpr 'root null 
            (parse-markdown 
              (string-join 
                (fix-draft-elements elements)
                ""))))
  

#| Probably won't use anymore: {{{
 |(define under-construction
 |  (->html
 |    '(div 
 |       ((class "construction-banner"))
 |       (span
 |         #x2622
 |         (strong "UNDER HEAVY CONSTRUCTION!")
 |         #x2622)
 |       (div #x2b07))))
 |
 |#
