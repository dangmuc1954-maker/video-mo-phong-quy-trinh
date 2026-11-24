"""Storyboard v2 'Chúc mừng bạn đã xây thành công Vạn Lý Trường Thành' — theo công thức video mẫu cầu Lư Câu (anh chỉnh 11/11/2026):
MÔ HÌNH MÔ PHỎNG 3D một quá trình xây dựng XUYÊN SUỐT, chia giai đoạn; mỗi giai đoạn trông ổn nhưng lộ khuyết điểm →
'người khôn như bạn' sửa → giai đoạn kế, tới khi xong; kết 'Xin chúc mừng bạn đã xây thành công…'. Chạy lại sau mỗi lần sửa."""
import json
from pathlib import Path

P = Path(__file__).resolve().parent
sc = []


def add(narr, action, camera, graphic=None):
    d = {"id": len(sc) + 1, "clip": f"scene_{len(sc) + 1:02d}.mp4", "setting": "site", "seconds": 10,
         "narration": narr, "action": action, "camera": camera}
    if sc:
        d["continue_from_previous"] = True
    if graphic:
        d["graphic"] = graphic
    sc.append(d)


def G(cue, lines, hold=2.6):
    return {"template": "kinetic_text", "cue": cue, "hold": hold, "anchor": "center", "data": {"lines": lines, "emphasis_index": 0}}


# 1 — mở: nhiệm vụ + mặt bằng
add("Thời loạn lạc, giặc phương Bắc hoành hành, chiến tranh nổ ra khắp nơi. Hoàng đế liền giao cho bạn một việc nhỏ xíu: xây một bức tường chặn giặc, dài hàng nghìn cây số. Nào, bắt tay vào việc thôi.",
    "3D construction simulation: a bare mountain ridge in soft morning light, surveyor stakes and rope lines appear one by one marking the route of a future wall along the crest, a few wooden shelters, the ground being cleared.",
    "smooth drone descent toward the ridge")
# 2-3 — giai đoạn 1: móng
add("Việc đầu tiên là nền móng. Bạn cho đục sườn núi thành từng bậc phẳng, rồi đặt những tảng đá lớn vào từng bậc. Nhìn vững chưa? Vững lắm… cho tới khi trời mưa.",
    "3D construction simulation: the steep rock slope is cut into level terraces by itself with stone chips flying, then huge squared stone blocks glide into each terrace and settle one by one, forming a stepped stone foundation along the slope.",
    "side-on cutaway view, slow push-in")
add("Mưa xuống, đất dưới đá bị nước cuốn đi, cả tảng đá trượt thẳng xuống chân núi, nhanh hơn cả giặc chạy. Thế là người khôn như bạn nện chặt nền, chèn đá hộc kín từng khe. Giờ móng mới thật sự vững.",
    "Cutaway cross-section simulation: rain water seeps under a foundation stone block (blue arrows), the soil washes away and the block tilts and slides; then rammed soil and small wedge stones fill every gap and the block locks firmly in place, yellow arrows show the support pushing up.",
    "side cutaway, static then slow push-in")
# 4-5 — giai đoạn 2: thân tường đất
add("Tiếp theo là thân tường. Thứ có sẵn nhiều nhất là đất, nên bạn đổ đất vào khuôn gỗ, nện từng lớp thật chặt, dựng lên một thân tường đất cao ngất.",
    "3D construction simulation: wooden plank formwork frames appear along the stone foundation, earth is poured in and wooden rammers pound each layer, the compacted rammed-earth wall core rises layer by layer, cutaway showing the layered earth.",
    "side cutaway, slow upward tilt")
add("Rẻ, nhanh, lại dễ làm. Nhưng mưa gió ở đây chẳng nể ai: tường đất bị xói từng mảng, nhão ra như bánh gặp nước. Người khôn như bạn hiểu ngay: phải bọc ngoài bằng thứ cứng hơn đất.",
    "Simulation: heavy rain falls on the tall rammed-earth wall core, water streaks run down, chunks of wet earth peel and melt away leaving a ragged eroded surface, puddles of mud pool at the base.",
    "medium shot, slow orbit")
# 6-7 — giai đoạn 3: gạch + vữa
add("Sau đó là lớp vỏ gạch. Bạn xây hàng loạt lò nung, gạch ra lò cứng như đá, rồi ốp kín mặt ngoài thân tường. Nhìn đẹp quá chừng!",
    "3D construction simulation: a row of brick kilns glow with fire, grey bricks stream out on carts then fly one by one onto the face of the earth wall core, forming a neat grey brick cladding rising along the wall.",
    "tracking shot from the kilns to the wall")
add("Đẹp thì đẹp, nhưng gạch xếp khô thế chỉ cần một cú đẩy là xô lệch. Thế là người khôn như bạn trộn vôi với cháo gạo nếp, trát giữa từng viên. Bạn gọi nó là: vữa gạo nếp.",
    "Macro 3D simulation: dry-stacked bricks slip and shift sideways under a push (yellow arrow); then thick creamy white lime and sticky-rice paste flows between the bricks and sets, the bricks lock tight.",
    "macro close-up, slow slide", G("vữa gạo nếp", ["VỮA", "GẠO NẾP"]))
# 8-9 — giai đoạn 4: mặt tường + thoát nước
add("Còn mặt tường thì sao? Bạn lát đá phẳng, đủ rộng cho lính và ngựa đi lại, thêm bậc thang và dốc nghiêng cho những đoạn núi dốc. Chắc xong thật rồi nhỉ?",
    "3D construction simulation: the top of the wall is paved with flat grey stone slabs forming a wide walkway, gentle ramps and stone steps appear on the steep sections as the wall climbs the hill.",
    "low tracking shot gliding along the walkway")
add("Chưa đâu bạn ơi. Nước mưa đọng trên mặt tường, thấm xuống lõi đất, vài mùa là phồng rộp. Thế là bạn cho đặt những máng đá nhô ra ngoài thân tường, để nước tự chảy đi.",
    "Cutaway simulation of the wall top in rain: water pools on the paved top and seeps down (blue arrows) into the earth core which swells and cracks; then carved stone spouts appear projecting from the outer face and the water shoots out and falls far away from the wall.",
    "side cutaway, then slow pull-back", G("máng đá", ["MÁNG ĐÁ", "THOÁT NƯỚC"]))
# 10-11 — giai đoạn 5: phòng thủ
add("Giờ đến phần phòng thủ. Mép ngoài bạn xây tường chắn có răng cưa, khoét những lỗ nhỏ để bắn tên mà không lộ mình. Bạn gọi đó là: lỗ châu mai.",
    "3D construction simulation: a low crenellated parapet rises along the outer edge of the walkway, small square loopholes are cut into it, light streams through them and small arrows fly out through the loopholes.",
    "slow dolly along the parapet", G("lỗ châu mai", ["LỖ", "CHÂU MAI"]))
add("Nhưng địch cứ áp sát chân tường, lính trên cao nhìn xuống mà bắn không tới, tức thật. Thế là người khôn như bạn xây tháp nhô hẳn ra ngoài, để bắn dọc theo tường từ hai phía. Bạn đặt tên nó là: địch đài.",
    "Simulation: tiny distant attackers with ladders reach the foot of the wall where the defenders on top cannot reach them (red dotted lines); then square watchtowers rise protruding from the wall face and glowing arrow lines now sweep along the wall base from both sides.",
    "slow orbit around the tower", G("địch đài", ["ĐỊCH", "ĐÀI"]))
# 12 — giai đoạn 6: báo tin
add("Còn chuyện báo tin nữa. Tường dài thế này, giặc đến mà tin chạy chậm là hỏng hết. Bạn dựng tháp trên các đỉnh đồi, ban ngày đốt khói, ban đêm đốt lửa. Bạn gọi đó là: phong hỏa đài.",
    "3D construction simulation time-lapse: beacon towers rise on hilltops along the wall; a white smoke column rises by day from the first, the next tower far away answers, then at dusk fire replaces smoke and the chain of lights runs along the ridge into the distance.",
    "static wide shot, slow push-in", G("phong hỏa đài", ["PHONG", "HỎA ĐÀI"]))
# 13 — giai đoạn 7: quan ải
add("Rồi đến những cửa ải. Người buôn bán vẫn phải qua lại, nên ở nơi hiểm yếu bạn dựng quan ải: tường dày, cổng bọc sắt, tháp canh cao. Sơn Hải Quan là cái tên nổi tiếng nhất.",
    "3D construction simulation: at a narrow mountain pass a fortress rises with thick gate towers and an iron-studded wooden gate, high walls climbing both slopes toward the sea on one side.",
    "crane shot rising to reveal the whole fortress")
# 14 — kéo dài
add("Giờ chỉ còn việc kéo dài. Bạn nối từng đoạn, vượt núi, băng sa mạc, mất không biết bao nhiêu mùa xuân và bao nhiêu đôi giày. Khảo sát năm hai nghìn không trăm mười hai ghi nhận hơn hai mươi mốt nghìn cây số.",
    "3D construction simulation: epic flight following the wall across mountains, then desert, then grasslands, new wall segments materializing ahead of the camera and linking together toward the horizon.",
    "fast smooth drone flight along the wall")
# 15 — khuyết điểm cuối: thời gian → bảo trì
add("Tưởng đâu hết chuyện, nhưng gió, mưa, băng tuyết vẫn đứng chờ. Thế là người khôn như bạn sắp lính tu sửa mỗi năm: chỗ nào nứt thì trét lại, chỗ nào lỏng thì xếp lại.",
    "Simulation time-lapse of one stretch of the finished wall through four seasons: snow, spring green, summer storm, autumn leaves; small cracks appear and are repaired by new bricks sliding into place.",
    "static wide shot on a long mountain ridge")
# 16 — chốt
add("Vậy là xong. Từ một sườn núi trơ trọi, bạn đã dựng nên bức tường dài nhất thế giới. Xin chúc mừng bạn, bạn đã xây thành công Vạn Lý Trường Thành!",
    "Golden sunset, the complete Great Wall winding across ridges to the horizon, warm light on the bricks, mist drifting in the valleys.",
    "slow crane pull-back from the wall", G("Vạn Lý Trường Thành", ["VẠN LÝ", "TRƯỜNG THÀNH"], 3.2))

sb = {
    "title": "Chuc mung ban da xay thanh cong Van Ly Truong Thanh", "mode": "tool", "type": "animation", "aspect": "9:16",
    "canvas": [1080, 1920], "fps": 30, "transition": True,
    "style": "clean bright 3D architectural construction SIMULATION animation (CGI engineering explainer): photorealistic stone, earth and brick materials, soft daylight, structures assemble step by step by themselves, cutaway cross-sections, glowing blue and yellow arrows showing forces and water flow, camera close to the objects, calm steady pacing",
    "settings": {"site": "a rugged green mountain ridge where a Ming dynasty Great Wall section is being built stage by stage, the same ridge and the same wall section in every shot, bright natural daylight, clear sky"},
    "lock": "no narration, no voices, soft ambient construction and nature sound only; no text, letters or logos anywhere; no people in close-up; keep the same ridge, wall section and lighting continuous from the previous video and show the construction progress accumulating",
    "negative": "text, letters, captions, watermark, logos, modern buildings, cars, cartoon look, deformed structures, close-up faces",
    "narration_voice": {"voice_id": "YeV2u3R2gzLArVTYTis8", "name": "giọng kể video vibe code", "reason": "giọng kể điềm tĩnh, rõ chữ, đã dùng tốt cho video giải thích"},
    "palette": ["#0F172A", "#FFFFFF", "#FACC15"], "subtitle_preset": "pop_word", "subtitle_size": 7,
    "edit_profile": {"genre": "tai_lieu_giai_thich", "goal": "người xem thấy mình thông minh, thích thú rồi chia sẻ", "audience": "16–45 tuổi, thích kiến thức thú vị TikTok",
                     "platform": "tiktok_9x16_150s", "presenter": "giong_ke_an", "mood": "hao_hung", "mood_key": "positive",
                     "arc": ["tò mò", "thích thú", "tự hào", "phấn khích"], "sensitivity": "khong", "pacing": "vua", "emphasis": "stamp_slam",
                     "subtitle": "story_pop", "sfx_style": "real_light", "climax_at": 0.95,
                     "hook": "nhiệm vụ bất khả thi giao cho 'bạn'", "ending": "chuc_mung_xay_thanh_cong"},
    "scenes": sc,
}
(P / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(sc), "cảnh", sum(len(s["narration"]) for s in sc), "ký tự lời kể")
