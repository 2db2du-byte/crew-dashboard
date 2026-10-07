// Show-style cartoon portraits for the crew (hand-drawn SVG, 120x120, thick black outlines).
const O = 'stroke="#111" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"';
const eye = (x, y, r = 9, px = 0, py = 0) =>
  `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff" ${O}/><circle cx="${x + px}" cy="${y + py}" r="2.2" fill="#111"/>`;

window.AVATARS = {
  claude: `<svg viewBox="0 0 120 120">
    <defs>
      <linearGradient id="visor" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff9a5c"/><stop offset=".5" stop-color="#ffd2a8"/><stop offset="1" stop-color="#d97757"/></linearGradient>
      <radialGradient id="glowC"><stop offset="0" stop-color="#ff9a5c" stop-opacity=".7"/><stop offset="1" stop-color="#ff9a5c" stop-opacity="0"/></radialGradient>
    </defs>
    <circle cx="60" cy="58" r="44" fill="url(#glowC)"/>
    <path d="M92 18 L104 30 L98 34 L78 58 L70 50 L92 30 Z" fill="#a9adb8" ${O}/>
    <circle cx="98" cy="24" r="9" fill="none" stroke="#111" stroke-width="3"/>
    <path d="M26 112 Q30 88 60 88 Q90 88 94 112 Z" fill="#2b2f3a" ${O}/>
    <path d="M44 90 L60 104 L76 90" fill="none" stroke="#d97757" stroke-width="5" stroke-linejoin="round"/>
    <g transform="translate(60 14)">
      ${[0,45,90,135,180,225,270,315].map((a) => `<path d="M0 0 L0 -11" transform="rotate(${a})" stroke="#d97757" stroke-width="4.5" stroke-linecap="round"/>`).join("")}
      <circle r="3.5" fill="#ffd2a8" stroke="#111" stroke-width="2"/>
    </g>
    <path d="M60 22 L60 30" ${O}/>
    <rect x="30" y="30" width="60" height="58" rx="22" fill="#3a3f4c" ${O}/>
    <path d="M34 52 Q60 44 86 52 L86 64 Q60 72 34 64 Z" fill="#111" ${O}/>
    <path d="M37 54 Q60 47 83 54 L83 62 Q60 69 37 62 Z" fill="url(#visor)"/>
    <rect x="44" y="55" width="11" height="4" rx="2" fill="#fff"/>
    <rect x="65" y="55" width="11" height="4" rx="2" fill="#fff"/>
    <path d="M48 78 Q60 84 72 78" fill="none" ${O}/>
    <path d="M24 60 Q24 30 60 28 Q96 30 96 60" fill="none" stroke="#111" stroke-width="5"/>
    <rect x="18" y="52" width="12" height="20" rx="5" fill="#d97757" ${O}/>
    <rect x="90" y="52" width="12" height="20" rx="5" fill="#d97757" ${O}/>
    <path d="M24 70 Q28 86 46 84" fill="none" stroke="#111" stroke-width="3"/>
    <circle cx="47" cy="84" r="3.5" fill="#d97757" stroke="#111" stroke-width="2"/>
  </svg>`,

  rick: `<svg viewBox="0 0 120 120">
    <path d="M22 70 L8 54 L24 52 L10 30 L32 36 L30 12 L48 28 L60 6 L70 28 L88 12 L88 36 L110 30 L96 52 L112 54 L98 70 Z" fill="#b8e3f2" ${O}/>
    <path d="M30 108 L36 92 L84 92 L90 108 Z" fill="#f4f4f4" ${O}/>
    <path d="M50 92 L60 104 L70 92 Z" fill="#8fc8e0" ${O}/>
    <path d="M36 44 Q34 92 60 96 Q86 92 84 44 Q60 34 36 44 Z" fill="#f2dcc8" ${O}/>
    <path d="M38 50 L46 46 L52 50 L60 46 L68 50 L74 46 L82 50" fill="none" stroke="#9ad0e4" stroke-width="5" stroke-linecap="round"/>
    ${eye(49, 60, 9, 2, 1)}${eye(71, 60, 9, -2, 1)}
    <path d="M60 64 L57 75 L62 75" fill="none" ${O}/>
    <path d="M47 83 Q60 79 73 84" fill="none" ${O}/>
    <path d="M70 84 Q72 90 70 94" fill="none" stroke="#9fd7ec" stroke-width="2.5" stroke-linecap="round"/>
  </svg>`,

  morty: `<svg viewBox="0 0 120 120">
    <path d="M26 110 Q30 90 60 90 Q90 90 94 110 Z" fill="#f5e04f" ${O}/>
    <circle cx="60" cy="58" r="32" fill="#f4d8bf" ${O}/>
    <path d="M28 54 Q26 24 60 22 Q94 24 92 54 Q84 40 74 42 Q66 34 56 40 Q44 34 36 44 Z" fill="#6b3f1d" ${O}/>
    ${eye(48, 60, 10, 1, 0)}${eye(72, 60, 10, -1, 0)}
    <path d="M60 66 Q63 71 59 73" fill="none" ${O}/>
    <path d="M48 81 Q52 77 56 81 Q60 85 64 81 Q68 77 72 81" fill="none" ${O}/>
    <path d="M40 50 Q46 47 52 51 M68 51 Q74 47 80 50" fill="none" ${O}/>
  </svg>`,

  summer: `<svg viewBox="0 0 120 120">
    <path d="M24 98 Q20 60 34 34 Q60 10 86 34 Q100 60 96 98 Z" fill="#e8743b" ${O}/>
    <path d="M28 112 Q32 92 60 92 Q88 92 92 112 Z" fill="#e8619b" ${O}/>
    <ellipse cx="60" cy="60" rx="27" ry="31" fill="#f6dcc6" ${O}/>
    <path d="M33 50 Q40 24 60 26 Q82 24 88 52 Q74 38 60 36 Q46 38 33 50 Z" fill="#e8743b" ${O}/>
    <path d="M36 38 Q60 22 84 38" fill="none" stroke="#e8619b" stroke-width="5" stroke-linecap="round"/>
    ${eye(49, 61, 8.5, 1, 1)}${eye(71, 61, 8.5, -1, 1)}
    <path d="M41 50 L49 49 M71 49 L79 50" fill="none" ${O}/>
    <path d="M52 80 Q60 84 68 79" fill="none" ${O}/>
  </svg>`,

  beth: `<svg viewBox="0 0 120 120">
    <path d="M26 82 Q20 40 40 28 Q60 16 80 28 Q100 40 94 82 Q86 72 84 62 L36 62 Q34 72 26 82 Z" fill="#f2d16b" ${O}/>
    <path d="M28 112 Q32 92 60 92 Q88 92 92 112 Z" fill="#c7363c" ${O}/>
    <ellipse cx="60" cy="60" rx="26" ry="31" fill="#f4dac4" ${O}/>
    <path d="M34 52 Q38 28 62 28 Q86 30 86 54 Q72 40 54 42 Q42 44 34 52 Z" fill="#f2d16b" ${O}/>
    ${eye(49, 61, 8.5, 1, 1)}${eye(71, 61, 8.5, -1, 1)}
    <path d="M40 51 Q46 48 54 51 M66 51 Q74 48 80 51" fill="none" ${O}/>
    <path d="M51 80 Q60 85 69 80" fill="none" ${O}/>
    <circle cx="60" cy="104" r="4" fill="#f4f4f4" ${O}/>
  </svg>`,

  birdperson: `<svg viewBox="0 0 120 120">
    <path d="M24 112 Q28 88 60 88 Q92 88 96 112 Z" fill="#5d6b4a" ${O}/>
    <path d="M40 92 L60 112 L80 92" fill="none" stroke="#c8a24a" stroke-width="4"/>
    <path d="M34 70 Q26 30 54 20 Q64 14 74 22 Q92 30 88 70 Q84 90 60 92 Q38 90 34 70 Z" fill="#8a5a33" ${O}/>
    <path d="M44 20 L40 6 L52 16 M60 16 L62 2 L68 16" fill="#8a5a33" ${O}/>
    <path d="M42 46 Q60 40 80 46 Q78 70 60 74 Q44 70 42 46 Z" fill="#e8dcc4" ${O}/>
    ${eye(52, 52, 6, 1, 0)}${eye(70, 52, 6, -1, 0)}
    <path d="M54 60 L60 92 L66 60 Z" fill="#e8a33c" ${O}/>
  </svg>`,

  gearhead: `<svg viewBox="0 0 120 120">
    <path d="M30 112 Q34 92 60 92 Q86 92 90 112 Z" fill="#6d6f7a" ${O}/>
    <g fill="#a9adb8" ${O}>
      <path d="M60 14 L68 14 L70 24 L80 28 L88 21 L94 27 L88 36 L92 46 L102 47 L102 56 L92 58 L88 68 L94 76 L88 82 L80 76 L70 80 L68 90 L52 90 L50 80 L40 76 L32 82 L26 76 L32 68 L28 58 L18 56 L18 47 L28 46 L32 36 L26 27 L32 21 L40 28 L50 24 L52 14 Z"/>
    </g>
    <circle cx="60" cy="52" r="24" fill="#d8d3c4" ${O}/>
    ${eye(51, 48, 7, 1, 0)}${eye(69, 48, 7, -1, 0)}
    <path d="M48 62 Q60 70 72 62" fill="none" ${O}/>
    <path d="M44 40 L56 42 M64 42 L76 40" fill="none" ${O}/>
  </svg>`,

  unity: `<svg viewBox="0 0 120 120">
    <circle cx="60" cy="60" r="50" fill="none" stroke="#c77dff" stroke-width="3" stroke-dasharray="3 7" opacity=".8"/>
    <path d="M28 96 Q22 50 38 32 Q60 14 82 32 Q98 50 92 96 Z" fill="#f3d88a" ${O}/>
    <path d="M30 112 Q34 92 60 92 Q86 92 90 112 Z" fill="#3a3550" ${O}/>
    <ellipse cx="60" cy="60" rx="25" ry="30" fill="#f4dac4" ${O}/>
    <path d="M35 52 Q36 28 60 28 Q84 28 85 52 Q70 36 50 42 Q42 44 35 52 Z" fill="#f3d88a" ${O}/>
    <circle cx="49" cy="61" r="8" fill="#e7c6ff" ${O}/><circle cx="71" cy="61" r="8" fill="#e7c6ff" ${O}/>
    <circle cx="49" cy="61" r="3" fill="#9d4edd"/><circle cx="71" cy="61" r="3" fill="#9d4edd"/>
    <path d="M52 80 Q60 84 68 80" fill="none" ${O}/>
  </svg>`,

  "noob-noob": `<svg viewBox="0 0 120 120">
    <path d="M86 30 L100 110" stroke="#8a5a33" stroke-width="6" stroke-linecap="round"/>
    <path d="M92 104 L108 104 L112 116 L88 116 Z" fill="#e8e1c8" ${O}/>
    <path d="M36 112 Q38 94 60 94 Q82 94 84 112 Z" fill="#4f7ca8" ${O}/>
    <ellipse cx="60" cy="64" rx="30" ry="32" fill="#9fd1a8" ${O}/>
    <path d="M30 52 Q32 26 60 26 Q88 26 90 52 Z" fill="#4f7ca8" ${O}/>
    <path d="M26 52 L94 52" ${O}/>
    <circle cx="50" cy="66" r="5.5" fill="#fff" ${O}/><circle cx="70" cy="66" r="5.5" fill="#fff" ${O}/>
    <circle cx="51" cy="67" r="2" fill="#111"/><circle cx="69" cy="67" r="2" fill="#111"/>
    <path d="M48 82 Q60 92 72 82" fill="#5a2a2a" ${O}/>
  </svg>`,

  snoopy: `<svg viewBox="0 0 120 120">
    <path d="M30 120 Q34 100 60 100 Q86 100 90 120 Z" fill="#fff" ${O}/>
    <ellipse cx="62" cy="62" rx="34" ry="30" fill="#fff" ${O}/>
    <ellipse cx="92" cy="72" rx="16" ry="11" fill="#fff" ${O}/>
    <ellipse cx="106" cy="69" rx="7" ry="6" fill="#111"/>
    <path d="M38 38 C18 40 14 70 28 84 C38 88 44 74 42 56 Z" fill="#111" ${O}/>
    <path d="M66 54 q6 -6 12 0" fill="none" ${O}/>
    <path d="M74 86 q9 6 18 0" fill="none" ${O}/>
    <rect x="38" y="96" width="44" height="8" rx="4" fill="#e23b3b" ${O}/>
  </svg>`,

  woodstock: `<svg viewBox="0 0 120 120">
    <path d="M52 30 L48 14 M60 28 L62 10 M68 30 L76 16" fill="none" ${O}/>
    <ellipse cx="60" cy="68" rx="32" ry="36" fill="#f6d743" ${O}/>
    <path d="M30 76 Q14 70 18 88 Q28 90 34 84 Z" fill="#f6d743" ${O}/>
    <path d="M90 76 Q106 70 102 88 Q92 90 86 84 Z" fill="#f6d743" ${O}/>
    <path d="M50 56 L56 58 M70 58 L76 56" fill="none" ${O}/>
    <path d="M56 70 L70 70 L63 78 Z" fill="#e8a33c" ${O}/>
    <path d="M48 104 L44 116 M72 104 L76 116" fill="none" ${O}/>
  </svg>`,

  "mr-meeseeks": `<svg viewBox="0 0 120 120">
    <path d="M34 120 L38 98 Q60 92 82 98 L86 120 Z" fill="#7ec8e8" ${O}/>
    <ellipse cx="60" cy="56" rx="30" ry="42" fill="#7ec8e8" ${O}/>
    <path d="M44 22 Q48 16 52 22" fill="none" ${O}/>
    ${eye(48, 46, 11, 2, 0)}${eye(72, 46, 11, -2, 0)}
    <path d="M40 66 Q60 96 80 66 Z" fill="#7a2232" ${O}/>
    <path d="M44 67 L76 67 L74 72 L46 72 Z" fill="#fff"/>
    <path d="M52 86 Q60 80 68 86 Q60 92 52 86 Z" fill="#e86b7e"/>
  </svg>`,
};
