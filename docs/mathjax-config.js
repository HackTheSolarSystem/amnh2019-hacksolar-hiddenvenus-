/*
 * Source: <http://docs.mathjax.org/en/latest/web/configuration.html>
 * You must also put the defer keyword in the script tag that loads
 * this script and the script that loads mathjax. This script has to
 * be run before the mathjax script. Defer makes sure they're run in
 * order while not blocking page rendering.
 */
window.MathJax = {
    tex: {
        /* Done this way to avoid racket's markdown module from trying
         * to replace these with script tags
         */
        inlineMath: [['\\-(', '\\-)']]
    },
    chtml: {
        scale: .8,
    }
};
