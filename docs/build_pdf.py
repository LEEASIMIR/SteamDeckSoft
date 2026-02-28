"""Generate SoftDeck_Guide.pdf from GUIDE.md content."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Font setup (Windows Korean font) ---
FONT_PATHS = [
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/malgunbd.ttf",
]

pdfmetrics.registerFont(TTFont("Malgun", FONT_PATHS[0]))
pdfmetrics.registerFont(TTFont("MalgunBold", FONT_PATHS[1]))
pdfmetrics.registerFontFamily("Malgun", normal="Malgun", bold="MalgunBold")

# --- Colors ---
BLACK = HexColor("#000000")
DARK = HexColor("#1a1a1a")
GRAY = HexColor("#666666")
LIGHT_GRAY = HexColor("#f5f5f5")
ACCENT = HexColor("#e94560")
WHITE = HexColor("#ffffff")
TABLE_HEADER_BG = HexColor("#222222")
TABLE_ALT_BG = HexColor("#f9f9f9")
TABLE_BORDER = HexColor("#cccccc")
CODE_BG = HexColor("#f0f0f0")

# --- Styles ---
styles = getSampleStyleSheet()

s_title = ParagraphStyle(
    "DocTitle", fontName="MalgunBold", fontSize=22, leading=28,
    textColor=BLACK, alignment=TA_CENTER, spaceAfter=6,
)
s_subtitle = ParagraphStyle(
    "DocSubtitle", fontName="Malgun", fontSize=11, leading=14,
    textColor=GRAY, alignment=TA_CENTER, spaceAfter=20,
)
s_h1 = ParagraphStyle(
    "H1", fontName="MalgunBold", fontSize=16, leading=22,
    textColor=BLACK, spaceBefore=24, spaceAfter=10,
)
s_h2 = ParagraphStyle(
    "H2", fontName="MalgunBold", fontSize=13, leading=18,
    textColor=DARK, spaceBefore=16, spaceAfter=8,
)
s_body = ParagraphStyle(
    "Body", fontName="Malgun", fontSize=10, leading=16,
    textColor=DARK, spaceAfter=6,
)
s_body_bold = ParagraphStyle(
    "BodyBold", fontName="MalgunBold", fontSize=10, leading=16,
    textColor=DARK, spaceAfter=6,
)
s_bullet = ParagraphStyle(
    "Bullet", fontName="Malgun", fontSize=10, leading=16,
    textColor=DARK, leftIndent=16, spaceAfter=3,
    bulletIndent=4, bulletFontSize=10,
)
s_code = ParagraphStyle(
    "Code", fontName="Courier", fontSize=9, leading=13,
    textColor=DARK, backColor=CODE_BG, leftIndent=12,
    spaceAfter=8, spaceBefore=4, borderPadding=6,
)
s_note = ParagraphStyle(
    "Note", fontName="Malgun", fontSize=9, leading=14,
    textColor=GRAY, leftIndent=12, spaceAfter=8,
)
s_table_header = ParagraphStyle(
    "TableHeader", fontName="MalgunBold", fontSize=9, leading=13,
    textColor=WHITE, alignment=TA_CENTER,
)
s_table_cell = ParagraphStyle(
    "TableCell", fontName="Malgun", fontSize=9, leading=13,
    textColor=DARK, alignment=TA_CENTER,
)
s_table_cell_left = ParagraphStyle(
    "TableCellLeft", fontName="Malgun", fontSize=9, leading=13,
    textColor=DARK,
)


def hr():
    return HRFlowable(width="100%", thickness=0.5, color=TABLE_BORDER, spaceAfter=12, spaceBefore=8)


def make_table(headers, rows, col_widths=None):
    """Create a styled table."""
    data = [[Paragraph(h, s_table_header) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), s_table_cell if i == 0 else s_table_cell_left) for i, c in enumerate(row)])

    if col_widths is None:
        col_widths = [None] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "MalgunBold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT_BG))
    t.setStyle(TableStyle(style_cmds))
    return t


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )

    story = []

    # ===== Title =====
    story.append(Spacer(1, 30))
    story.append(Paragraph("SoftDeck", s_title))
    story.append(Paragraph("시작 가이드", ParagraphStyle(
        "Sub", fontName="Malgun", fontSize=14, leading=18,
        textColor=ACCENT, alignment=TA_CENTER, spaceAfter=8,
    )))
    story.append(Paragraph(
        "키보드 넘패드를 나만의 컨트롤러로 만들어 주는 앱",
        s_subtitle,
    ))
    story.append(hr())

    # ===== 1. 처음 실행하면 =====
    story.append(Paragraph("1. 처음 실행하면", s_h1))
    story.append(Paragraph(
        "앱을 실행하면 화면 위쪽에 작은 검은색 창이 나타납니다. "
        "왼쪽에 폴더 트리, 오른쪽에 3x3 버튼 그리드가 표시됩니다.",
        s_body,
    ))
    story.append(Paragraph(
        "기본으로 미디어 컨트롤, 시스템 모니터, 앱 바로가기 등이 세팅되어 있어서 "
        "별도 설정 없이 바로 사용할 수 있습니다.",
        s_body,
    ))
    story.append(Spacer(1, 8))

    # ===== 2. 넘패드로 조작하기 =====
    story.append(Paragraph("2. 넘패드로 조작하기", s_h1))
    story.append(Paragraph(
        "<b>Num Lock을 끄세요.</b> 그러면 넘패드가 버튼 리모컨이 됩니다.",
        s_body,
    ))

    story.append(Paragraph("넘패드 키 → 버튼 위치 매핑", s_h2))
    story.append(make_table(
        ["넘패드 키", "버튼 위치"],
        [
            ["Num 7 / 8 / 9", "1행 (왼쪽 → 오른쪽)"],
            ["Num 4 / 5 / 6", "2행"],
            ["Num 1 / 2 / 3", "3행"],
            ["Num 0", "뒤로가기 (상위 폴더)"],
        ],
        col_widths=[80 * mm, 80 * mm],
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Num Lock에 따른 동작", s_h2))
    story.append(make_table(
        ["Num Lock", "넘패드 키", "창 상태"],
        [
            ["OFF", "버튼 덱 조작", "창 표시"],
            ["ON", "일반 숫자 입력", "창 숨김"],
        ],
        col_widths=[50 * mm, 55 * mm, 55 * mm],
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Ctrl + ` (백틱) — 언제든 창 표시/숨기기 토글 (Num Lock 상관없이)", s_note))

    # ===== 3. 기본 버튼 =====
    story.append(Paragraph("3. 기본으로 들어있는 버튼", s_h1))

    story.append(Paragraph("메인 화면", s_h2))
    story.append(make_table(
        ["Num 7", "Num 8", "Num 9"],
        [
            ["볼륨 -", "음소거", "볼륨 +"],
            ["이전 곡 (Num 4)", "재생/정지 (Num 5)", "다음 곡 (Num 6)"],
            ["CPU 사용률 (Num 1)", "RAM 사용률 (Num 2)", "Apps 폴더 (Num 3)"],
        ],
        col_widths=[53 * mm, 53 * mm, 53 * mm],
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Apps 폴더 (Num 3으로 진입)", s_h2))
    story.append(make_table(
        ["Num 7", "Num 8", "Num 9"],
        [
            ["계산기", "메모장", "탐색기"],
            ["작업관리자 (Num 4)", "화면캡처 (Num 5)", "CMD (Num 6)"],
            ["Shortcuts 폴더 (Num 1)", "YouTube (Num 2)", "Google (Num 3)"],
        ],
        col_widths=[53 * mm, 53 * mm, 53 * mm],
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Shortcuts 폴더 (Apps에서 Num 1로 진입)", s_h2))
    story.append(make_table(
        ["Num 7", "Num 8", "Num 9"],
        [
            ["복사", "붙여넣기", "되돌리기"],
            ["잘라내기 (Num 4)", "전체선택 (Num 5)", "다시실행 (Num 6)"],
            ["저장 (Num 1)", "스크린샷 (Num 2)", "PC 잠금 (Num 3)"],
        ],
        col_widths=[53 * mm, 53 * mm, 53 * mm],
    ))
    story.append(Paragraph("Num 0을 누르면 이전 폴더로 돌아갑니다.", s_note))

    # ===== 4. 내 버튼 만들기 =====
    story.append(Paragraph("4. 내 버튼 만들기", s_h1))
    story.append(Paragraph(
        "버튼을 <b>마우스 우클릭</b> → <b>Edit Button</b>을 누르면 편집 창이 열립니다.",
        s_body,
    ))

    story.append(Paragraph("액션 타입", s_h2))
    story.append(make_table(
        ["하고 싶은 것", "액션 타입", "예시"],
        [
            ["프로그램 실행", "Launch App", "notepad.exe, calc.exe"],
            ["단축키 보내기", "Hotkey", "ctrl+c, alt+f4"],
            ["텍스트 자동 입력", "Text Input", "자주 쓰는 문장"],
            ["음악/볼륨 조절", "Media Control", "재생, 정지, 볼륨"],
            ["CPU/RAM 확인", "System Monitor", "(자동 업데이트)"],
            ["다른 폴더로 이동", "Navigate Folder", "폴더 선택"],
            ["웹사이트 열기", "Open URL", "https://youtube.com"],
            ["여러 동작 연속 실행", "Macro", "핫키 → 대기 → 텍스트"],
        ],
        col_widths=[45 * mm, 40 * mm, 75 * mm],
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("버튼 꾸미기", s_h2))
    story.append(make_table(
        ["항목", "설명"],
        [
            ["Label", "버튼에 표시할 이름"],
            ["Icon", "아이콘 이미지 (png, jpg, ico). 아이콘 위에 글씨 표시"],
            ["Label Color", "글씨 색상 (색상 버튼 클릭 또는 #ff0000 입력)"],
            ["Font Size", "글씨 크기 (기본 15px)"],
        ],
        col_widths=[40 * mm, 120 * mm],
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>버튼 복사:</b> 원본 버튼 우클릭 → Copy Button → 빈 버튼 우클릭 → Paste Button",
        s_body,
    ))

    # ===== 5. 폴더로 정리하기 =====
    story.append(Paragraph("5. 폴더로 정리하기", s_h1))
    story.append(Paragraph(
        "버튼이 9개로 부족하면 폴더를 만들어 용도별로 나눌 수 있습니다. "
        "폴더 안에 폴더를 만들 수 있어서 원하는 만큼 버튼을 늘릴 수 있습니다.",
        s_body,
    ))
    story.append(Paragraph(
        "왼쪽 폴더 트리에서 <b>우클릭</b> → <b>New Sub-Folder</b>로 폴더를 생성하고, "
        "버튼에 <b>Navigate Folder</b> 액션을 지정하면 넘패드로 폴더 이동이 가능합니다.",
        s_body,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("자동 폴더 전환", s_h2))
    story.append(Paragraph(
        "폴더에 앱을 매핑하면 해당 앱 사용 시 자동으로 폴더가 전환됩니다.",
        s_body,
    ))
    story.append(Paragraph("  1. 폴더 우클릭 → Edit (Mapped Apps)", s_bullet))
    story.append(Paragraph("  2. 프로그램 이름 추가 (예: chrome.exe)", s_bullet))
    story.append(Paragraph("  3. 해당 프로그램 포커스 시 자동 전환", s_bullet))

    # ===== 6. 창 다루기 =====
    story.append(Paragraph("6. 창 다루기", s_h1))
    story.append(make_table(
        ["조작", "방법"],
        [
            ["창 이동", "상단 바 드래그"],
            ["크기 조절", "창 가장자리 드래그"],
            ["숨기기/보이기", "Num Lock 토글 또는 Ctrl + `"],
            ["투명도", "상단 바 슬라이더 (20%~100%)"],
            ["트레이로", "▼ 버튼 또는 창 닫기 (종료 아님)"],
            ["완전 종료", "트레이 우클릭 → Quit"],
        ],
        col_widths=[50 * mm, 110 * mm],
    ))

    # ===== 7. 설정 =====
    story.append(Paragraph("7. 설정", s_h1))
    story.append(Paragraph("상단 바 <b>우클릭</b> → <b>Settings</b>", s_body))
    story.append(make_table(
        ["설정", "설명", "기본값"],
        [
            ["Button Size", "버튼 크기", "100px"],
            ["Button Spacing", "버튼 간격", "8px"],
            ["Auto-switch", "활성 앱 기반 폴더 자동 전환", "ON"],
            ["Always on top", "다른 창 위에 항상 표시", "ON"],
            ["Opacity", "창 투명도", "100%"],
        ],
        col_widths=[45 * mm, 75 * mm, 40 * mm],
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>설정 백업:</b> 상단 바 우클릭 → Export Config / Import Config로 JSON 파일 저장/불러오기",
        s_body,
    ))

    # ===== 8. 게임할 때 =====
    story.append(Paragraph("8. 게임할 때", s_h1))
    story.append(make_table(
        ["게임 모드", "넘패드 조작", "창 보임"],
        [
            ["보더리스 (창모드)", "O", "O"],
            ["전체화면", "O", "X"],
        ],
        col_widths=[55 * mm, 50 * mm, 55 * mm],
    ))
    story.append(Paragraph(
        "대부분의 게임은 보더리스 모드를 사용하므로 정상 동작합니다. "
        "버튼 클릭 시 게임 포커스가 빠지지 않습니다.",
        s_note,
    ))

    # ===== 단축키 요약 =====
    story.append(hr())
    story.append(Paragraph("단축키 요약", s_h1))
    story.append(make_table(
        ["키", "동작"],
        [
            ["Num 1~9 (Num Lock OFF)", "버튼 실행"],
            ["Num 0", "상위 폴더로 이동"],
            ["Num Lock 토글", "버튼 모드 / 숫자 모드 전환 + 창 표시/숨김"],
            ["Ctrl + `", "창 표시/숨기기"],
            ["버튼 우클릭", "편집 / 복사 / 붙여넣기 / 초기화"],
            ["상단 바 우클릭", "설정 / 내보내기 / 가져오기"],
            ["트레이 우클릭", "표시 / 설정 / 위치초기화 / 종료"],
        ],
        col_widths=[60 * mm, 100 * mm],
    ))

    doc.build(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    out = str(Path(__file__).parent / "SoftDeck_Guide.pdf")
    build_pdf(out)
