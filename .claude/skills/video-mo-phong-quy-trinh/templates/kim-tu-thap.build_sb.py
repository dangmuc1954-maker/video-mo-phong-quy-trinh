"""MẪU CHUẨN: storyboard video mô phỏng quy trình xây Kim tự tháp Giza (Kiểu B "xé toạc").
Copy file này thành projects/<slug>/build_sb.py, sửa BÀI TOÁN GỐC + cảnh. Chạy: python projects/<slug>/build_sb.py

BÀI TOÁN GỐC
  Công trình : Kim tự tháp Giza (Khufu)
  Mở đầu     : Kiểu B — xé toạc (lăng mộ, khó nêu nhu cầu)
  Mục tiêu   : lăng mộ tồn tại mãi mãi
  Thử thách  : nền cát lệch, cắt đá không có máy, kéo đá trên cát, đá ở bên kia sông, đưa đá lên cao, sức đè lên phòng mộ
  Câu chốt   : Xin chúc mừng bạn, bạn đã xây thành công Kim tự tháp Giza!
Kiểm nguồn trước khi làm thật: facts.json (2,3 triệu khối; cao ban đầu ~146 m; 5 buồng giảm tải; tranh mộ Djehutihotep té nước;
nhật ký Merer chở đá Tura bằng thuyền; cao nhất thế giới ~3.800 năm). Giả thuyết: rãnh nước làm mốc, dốc đắp.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent
sc = []


def add(narr, beats, camera, graphic=None, **kw):
    d = {"id": len(sc) + 1, "clip": f"scene_{len(sc) + 1:02d}.mp4", "setting": "site", "seconds": 10,
         "narration": narr, "beats": beats, "camera": camera, **kw}
    if sc and not kw.get("real_photo"):
        d["continue_from_previous"] = True
    if graphic:
        d["graphic"] = {"template": "kinetic_text", "cue": graphic[0], "hold": 2.8, "anchor": "center",
                        "data": {"lines": graphic[1], "emphasis_index": 0}}
    sc.append(d)


add("Nếu bạn xé toạc Kim tự tháp ra, bạn sẽ thấy bên trong là hàng triệu khối đá xếp khít, những đường hầm và phòng mộ giấu kín.",
    [["0-2s", "the complete white-cased pyramid stands in the desert, three-quarter view; on the word 'tear open' it splits vertically into two halves that slide apart"],
     ["2-5s", "the camera pushes into the gap; a glowing section plane sweeps across the cut face, revealing the stacked limestone courses layer by layer"],
     ["5-9s", "X-ray view: the descending passage, the Grand Gallery and the burial chambers light up as glowing orange paths inside the semi-transparent stone"]],
    "slow push-in toward the cut face", hoan_thanh=True, da_co=["the complete white-cased structure"], chua_co=[])
add("Nhưng mọi thứ bắt đầu từ những viên đá đầu tiên dưới đây. Pharaoh giao cho bạn một việc nhỏ xíu: xây một lăng mộ tồn tại mãi mãi.",
    [["0-4s", "reverse time-lapse: the stone courses retract quickly from the top down until only the first course remains on the ground"],
     ["4-10s", "the camera zooms down to a single corner block of the first course, which gets a glowing outline; the empty construction site with survey stakes behind it"]],
    "continuous zoom from wide view down to the corner block", tua_lai=True, da_co=["one first course of stone blocks on bare sand"], chua_co=["upper stone courses","white casing stones","capstone","construction ramp","canal","boats"])
add("Việc đầu tiên là mặt bằng. Nền mà lệch một chút, lên tới đỉnh sẽ lệch cả mét, tháp méo như bánh đổ khuôn.",
    [["0-3s", "rewind to uneven sand dunes; side cutaway through the ground shows a loose sand layer over flat bedrock"],
     ["3-6s", "a stone block set on the uneven sand tilts slightly, a red angle marker appears at its base"],
     ["6-9s", "a ghosted translucent wireframe pyramid rises from the tilted base and leans visibly to one side, a red line marks the error at the apex, then it fades"]],
    "side cutaway view, slow push-in", tua_lai=True, da_co=["bare uneven sand dunes","bedrock below","one tilted stone block"], chua_co=["stone courses","white casing stones","capstone","construction ramp","canal","boats","inner chambers"])
add("Đứng nhìn vũng nước, bạn chợt hiểu: mặt nước luôn phẳng. Bạn đào rãnh, đổ nước làm mốc để san nền. Nhiều nhà nghiên cứu tin đó là cách thợ xưa đã làm.",
    [["0-3s", "the sand is swept away to bedrock; a small puddle with a glowing blue horizontal line along its surface"],
     ["3-7s", "a grid of narrow trenches cuts itself into the bedrock and fills with water; cutaway shows every water surface on the same blue level line"],
     ["7-11s", "the rock between the trenches is chiselled down to the blue marks, the water drains, leaving a perfectly flat platform"]],
    "top-down three-quarter view with side cutaway", ("làm mốc", ["MẶT NƯỚC", "LÀM MỐC"]), da_co=["flat bedrock platform with water-filled trenches"], chua_co=["stone courses","white casing stones","capstone","construction ramp","canal","boats","inner chambers"])
add("Tiếp theo là đá. Không có máy cắt, bạn chỉ có đục đồng, búa đá và rất nhiều kiên nhẫn: khoét rãnh quanh từng khối, rồi bẩy cho nó tách khỏi vách núi.",
    [["0-3s", "the camera pans to a limestone quarry face beside the site"],
     ["3-6s", "copper chisels and round stone pounders move by themselves, chipping a channel; stone chips fly"],
     ["6-11s", "cutaway of the rock face: channels around all four sides of a block, wooden levers under it; exploded view as the block cracks free and lifts out along its axis"]],
    "side cutaway of the quarry face", da_co=["flat platform","limestone quarry face"], chua_co=["stone courses","white casing stones","capstone","construction ramp","boats","inner chambers"])
add("Mỗi khối nặng vài tấn. Kéo trên cát thì cát cứ dồn đống trước mũi xe, kéo mãi không nhích. Nhưng bạn không chịu bỏ cuộc.",
    [["0-3s", "the block is lashed onto a wooden sledge, a big red arrow shows its weight; side cutaway shows the loose sand under the runners"],
     ["3-7s", "the sledge is dragged forward, loose sand piles up in front of its nose, the sledge sinks, a red friction arrow grows larger"],
     ["7-10s", "the sledge stops, slow push-in on the sand pile"]],
    "low side cutaway", da_co=["flat platform","quarry","one block on a wooden sledge"], chua_co=["stone courses","white casing stones","capstone","construction ramp","boats","inner chambers"])
add("Một lần nghỉ ngơi, bạn để ý cát ướt thì chặt lại. Thế là bạn té nước trước mũi xe, kéo nhẹ hẳn. Tranh trong một ngôi mộ cổ vẫn còn vẽ cảnh này.",
    [["0-4s", "continuous zoom down to grain-level macro: on the left dry sand grains roll loosely, on the right wet grains are bridged by thin blue water films"],
     ["4-7s", "zoom back out: a clay jar tips water onto the sand in front of the sledge, the sand darkens and firms, the red friction arrow shrinks small"],
     ["7-10s", "the sledge glides smoothly; the image transitions into a flat ancient Egyptian wall-painting style panel of water poured in front of a sledge"]],
    "macro zoom then low tracking shot", da_co=["flat platform","quarry","sledge on wet sand"], chua_co=["stone courses","white casing stones","capstone","construction ramp","boats","inner chambers"])
add("Đá vôi trắng đẹp nhất lại nằm tận bên kia sông Nile. Thua keo này, bạn bày keo khác: đào kênh, chở đá bằng thuyền thẳng tới công trường.",
    [["0-3s", "diorama-style wide view of the Nile valley; a white limestone quarry on the far bank gets a glowing outline"],
     ["3-6s", "a canal digs itself from the river toward the plateau; side cutaway shows the water depth in the canal"],
     ["6-10s", "wooden boats carrying white blocks float along the canal and dock at a harbour below the construction site"]],
    "high three-quarter diorama view", da_co=["flat platform","quarry","sledge","canal","boats"], chua_co=["white casing stones","capstone","construction ramp","inner chambers"])
add("Tháp càng cao, đá càng khó đưa lên. Người ta cho rằng bạn đắp dốc men theo thân tháp, cao tới đâu nối dốc tới đó.",
    [["0-3s", "fast time-lapse: the stepped core rises course by course to about one third of its height"],
     ["3-9s", "X-ray view of the body shows the core blocks inside while a mud-brick and rubble ramp grows along the outside; sledges climb it; the ramp lengthens as the structure grows"]],
    "slow orbit around the rising structure", da_co=["stepped stone core up to one third of its height","construction ramp"], chua_co=["white casing stones","capstone","inner chambers"])
add("Rồi đến phòng mộ của pharaoh. Phía trên là hàng triệu tấn đá đè xuống, trần mà nứt là sập cả căn phòng.",
    [["0-4s", "the camera flies through the wall into the ascending passage, up the Grand Gallery, into the granite burial chamber"],
     ["4-8s", "side section through the core: the stone mass above is covered with red arrows pushing down; the granite ceiling beams bend and crack lines spread"]],
    "camera flies inside, then side section", da_co=["stepped stone core","construction ramp","granite burial chamber ceiling"], chua_co=["white casing stones","capstone"])
add("Ngàn cân treo sợi tóc, bạn lại sáng lên ý tưởng: chồng năm tầng khoang rỗng phía trên, đỉnh là mái đá chữ A đẩy sức nặng sang hai bên. Người khôn như bạn gọi chúng là buồng giảm tải.",
    [["0-3s", "time freezes and the cracks reverse and disappear"],
     ["3-8s", "exploded view: five narrow stacked compartments separated by granite beams assemble upward above the chamber ceiling, topped by a gabled limestone A-shaped roof"],
     ["8-12s", "animated red arrows hit the A-shaped roof and split diagonally to both sides; the chamber ceiling stays intact"]],
    "side section, slow push-in", ("buồng giảm tải", ["BUỒNG", "GIẢM TẢI"]), da_co=["stepped stone core","construction ramp","burial chamber","relieving compartments"], chua_co=["white casing stones","capstone"])
add("Cuối cùng là lớp áo. Bạn ốp đá vôi trắng ra ngoài, mài phẳng đến mức cả kim tự tháp sáng lóa dưới nắng sa mạc, rồi đặt viên đá chóp lên đỉnh.",
    [["0-4s", "the stepped core reaches full height and the ramp retracts"],
     ["4-8s", "white limestone casing blocks clad the outside; a section plane shows the thin casing over the thick core; a polishing pass moves from the top down, the faces turn smooth and bright"],
     ["8-11s", "the capstone lowers and locks onto the apex with a flash of light"]],
    "three-quarter view rising toward the apex", da_co=["stepped stone core at full height","burial chamber"], chua_co=[])
add("Hơn hai triệu khối đá, cao gần một trăm năm mươi mét. Gần bốn nghìn năm, không công trình nào của con người cao hơn nó.",
    [["0-5s", "the finished pyramid rotates 360 degrees in the desert; for a moment the outer layers turn semi-transparent showing the whole interior, then become solid again"],
     ["5-9s", "the camera pulls back far; the pyramid shines white with a long shadow"]],
    "slow orbit then pull-back", ("không công trình", ["KIM TỰ THÁP", "GIZA"]), hoan_thanh=True, da_co=["the complete white-cased structure"], chua_co=[])
add("Xin chúc mừng bạn, bạn đã xây thành công Kim tự tháp Giza!",
    [["0-5s", "real photograph of the Great Pyramid of Giza at sunset, slow zoom"]],
    "slow zoom", real_photo="File:Kheops-Pyramid.jpg", source="Wikimedia Commons", transition_in="Lóa sáng rạng rỡ")

sb = {
    "title": "Chuc mung ban da xay thanh cong Kim tu thap Giza", "mode": "tool", "type": "animation", "aspect": "9:16",
    "canvas": [1080, 1920], "fps": 30, "transition": True,
    "style": "3D technical simulation animation, clean simplified CGI models, smooth uniform materials, bright even daylight, educational engineering visualization like a construction documentary diagram, objects animate into place step by step by themselves, cutaway cross-sections and colored force arrows, clear 3D depth with foreground and background layers",
    "ten_cong_trinh": ["pyramid"],
    "settings": {"site": "a pale yellow desert plateau construction site beside a wide river valley, clear blue sky, bright even daylight, the same site in every shot"},
    "lock": "no narration, no voices, soft ambient sound only; no text, letters or logos anywhere; no people in close-up; same construction site continuing from the previous video, show ONLY what has been built so far, construction progress accumulating",
    "negative": "photorealistic, cinematic film look, live-action footage, drone footage, lens flare, text, letters, captions, watermark, logos, modern buildings, cars, cartoon characters, close-up faces, deformed structures",
    "narration_voice": {"voice_id": "YeV2u3R2gzLArVTYTis8", "name": "giọng kể video vibe code", "reason": "giọng kể điềm tĩnh, rõ chữ"},
    "palette": ["#0F172A", "#FFFFFF", "#FACC15"], "subtitle_preset": "pop_word", "subtitle_size": 7,
    "edit_profile": {"genre": "kien_truc_mo_phong", "goal": "người xem thấy mình thông minh, thích thú rồi chia sẻ", "audience": "16–45 tuổi, thích kiến thức thú vị",
                     "platform": "tiktok_9x16_135s", "presenter": "giong_ke_an", "mood": "hao_hung", "mood_key": "positive",
                     "arc": ["tò mò", "thử thách", "à ra vậy", "tự hào"], "sensitivity": "khong", "pacing": "vua", "emphasis": "stamp_slam",
                     "subtitle": "story_pop", "sfx_style": "real_light", "climax_at": 0.85, "ending": "chuc_mung_xay_thanh_cong", "music_start": 0},
    "scenes": sc,
}
(P / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(sc), "cảnh,", sum(len(s["narration"]) for s in sc), "ký tự lời kể")
