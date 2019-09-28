#lang pollen
/* Color Picker: <http://www.hslpicker.com/#bd9d00>*/
◊(define construction-color "hsl(50, 100%, 73%)")
◊(define draft-color "hsl(50, 0%, 50%)")
code{
    white-space: pre-wrap;
    font-family: "fira mono",monospace;
    font-size: .9rem;
}
span.smallcaps{font-variant: small-caps;}
span.underline{text-decoration: underline;}
div.column{display: inline-block; vertical-align: top; width: 50%;}

html {
    margin: auto;
    max-width: 40rem;
    font-family: "source sans pro",sans-serif;
    line-height: 1.3;
    font-size: 20px;
}

/* While this works, I need to work on it better.
 * Smaller screen should have a special nav-bar style to make
 * navigation easy using fingers, and should change font sizes.
 * Should also pay special attention to the noodle pictures, like in
 * index.
 *html { font-size: 2.4vw; }
 *@media all and (min-width:1000px) { html { font-size: 24px; } }
 *@media all and (max-width:520px) { html{ font-size: 18px; } }
 */

body {
    text-rendering: optimizeLegibility;
    padding-top: 3rem;
    box-sizing: border-box;
}

/*Make sure images obey the site-wide width*/
.img-container {
    max-width: 45rem;
}

/*Source: <https://stackoverflow.com/questions/12991351/css-force-image-resize-and-keep-aspect-ratio>*/
.img-container img {
    width: 100%;
    height: auto;
    object-position: center center;
    object-fit: scale-down;
}

p.caption {
    text-align: center;
}

/*
 *The site nav in practical typography is larger than the text body
 *area. There's a left margin where things can go, like notes and
 *section titles. The nav goes from the right side of the body to the
 *very left of the content on the page.
 */
#site-nav {
    display: flex;
    justify-content: center;
    border-top: 1px solid;
    border-bottom: 1px solid;
    font-size: 90%;
}

.nav-spacer {
    box-sizing: border-box;
    margin-left: 1.5rem;
    margin-right: 1.5rem;
    text-align: center;
    border-left: 1px solid;
}

pre {
    padding: 1rem;
    background-color: #f6f8fa;
    font-size: .85rem;
}

.construction-banner {
    height: 4rem;
    position: relative;
    background-color: ◊|construction-color|;
}

/*Source: <https://www.w3schools.com/howto/howto_css_center-vertical.asp>*/
.construction-banner span {
    position: absolute;

    /* Make the span the width of the banner and then align all text to
     * the center. This gives the horizontal centering without
     * squeezing the text into a small portion of the box.*/
    text-align: center;
    width: 100%;
}

.construction-banner div {
    position: absolute;
    top: 100%;
    transform: translateY(-100%);

    /* Make the span the width of the banner and then align all text to
     * the center. This gives the horizontal centering without
     * squeezing the text into a small portion of the box.*/
    text-align: center;
    width: 100%;
    font-size: 1.5rem;
}

a {
    font-variant: small-caps;
    text-decoration: none;
}

h1 {
    font-size: 1.1rem;
    padding: 0;
    margin: 0;
    font-weight: bold;
}

/* Draft Mode Options: {{{ ******************************************/
◊draft{

body {
    border-left: 1px solid black;
    border-right: 1px solid black;
}

.todo {
    background-color: ◊|construction-color|;
}
.draft {
    opacity: 0.5;
}

}
/* }}} **************************************************************/
