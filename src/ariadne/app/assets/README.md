# Fonts

Two variable faces, both under the SIL Open Font License 1.1, whose full text
sits beside each one.

| File | Family | Where it is used |
|---|---|---|
| `Manrope[wght].ttf` | Manrope | The chrome — rail, facts, controls |
| `Literata[opsz,wght].ttf` | Literata | Names and headings, which are this application's reading surface |

GTK resolves fonts through fontconfig, and fontconfig cannot see a Python
package. So an installed Ariadne puts these in a real font directory
(`/usr/share/fonts/truetype/ariadne` from the `.deb`, `/app/share/fonts` from
the Flatpak), and a checkout reaches them through `use_bundled_fonts()` in
`__init__.py`, which writes a fontconfig fragment naming this directory.

If either face is missing the chrome falls back to Cantarell and the layout is
unchanged.
