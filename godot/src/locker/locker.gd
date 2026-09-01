extends Node

## Locker catalog. Swapping a look is a skin, not a new operator.

const OP_CANCHO := "cancho"
const STYLE_DEFAULT := "default"
const STYLE_RANKED := "ranked"
const STYLE_NIGHT := "night"

const MINT := Color(0.35, 0.95, 0.78)
const BONE := Color(0.90, 0.88, 0.82)

var equipped_operator_id: String = OP_CANCHO
var equipped_style_id: String = STYLE_DEFAULT


func operator(id: String = "") -> OperatorDef:
	var key := id if id != "" else equipped_operator_id
	return _cancho() if key == OP_CANCHO else _cancho()


func style(id: String = "") -> OutfitStyle:
	var key := id if id != "" else equipped_style_id
	match key:
		STYLE_RANKED:
			return _ranked()
		STYLE_NIGHT:
			return _night()
		_:
			return _default()


func style_ids() -> PackedStringArray:
	return operator().style_ids


func equip_style(id: String) -> void:
	if id in style_ids():
		equipped_style_id = id


func cycle_style() -> String:
	var ids := style_ids()
	if ids.is_empty():
		return equipped_style_id
	var i := 0
	for n in ids.size():
		if ids[n] == equipped_style_id:
			i = n
			break
	equipped_style_id = ids[(i + 1) % ids.size()]
	return equipped_style_id


func apply_capsule(body: MeshInstance3D, collar: MeshInstance3D, arm: MeshInstance3D, stripe: MeshInstance3D, rust: MeshInstance3D, chest: MeshInstance3D, lifted: bool) -> void:
	var s := style()
	_paint(body, s.body)
	_paint(collar, s.body)
	_paint(arm, s.body)
	_paint(stripe, s.stripe if lifted else s.stripe_rest)
	_paint(rust, s.rust)
	if rust != null:
		rust.visible = s.rust_visible
	if stripe != null:
		stripe.visible = true
	if chest != null:
		chest.visible = s.chest_band
		_paint(chest, s.stripe)


func _paint(mesh: MeshInstance3D, color: Color) -> void:
	if mesh == null:
		return
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = color
	mesh.material_override = mat


func _cancho() -> OperatorDef:
	var op := OperatorDef.new()
	op.id = OP_CANCHO
	op.slot = 1
	op.display_name = "CANCHO"
	op.skeleton_id = "cancho_capsule"
	op.style_ids = PackedStringArray([STYLE_DEFAULT, STYLE_RANKED, STYLE_NIGHT])
	# VO is the operator, not the outfit.
	op.vo_lift = "Al aire."
	op.vo_hit = "Claro."
	op.vo_drop = "Al suelo."
	op.vo_win = "Se escribió."
	return op


func _default() -> OutfitStyle:
	var s := OutfitStyle.new()
	s.id = STYLE_DEFAULT
	s.body = Color(0.06, 0.07, 0.08)
	s.stripe = MINT
	s.stripe_rest = MINT
	s.chest_band = false
	s.rust = Color(0.55, 0.28, 0.18)
	s.rust_visible = true
	return s


func _ranked() -> OutfitStyle:
	var s := OutfitStyle.new()
	s.id = STYLE_RANKED
	s.body = Color(0.04, 0.05, 0.07)
	s.stripe = MINT
	s.stripe_rest = MINT
	s.chest_band = true
	s.rust = Color(0.45, 0.26, 0.2)
	s.rust_visible = true
	return s


func _night() -> OutfitStyle:
	var s := OutfitStyle.new()
	s.id = STYLE_NIGHT
	s.body = Color(0.02, 0.02, 0.025)
	s.stripe = MINT
	s.stripe_rest = Color(0.12, 0.35, 0.28)
	s.chest_band = false
	s.rust = Color(0.2, 0.1, 0.08)
	s.rust_visible = true
	return s
