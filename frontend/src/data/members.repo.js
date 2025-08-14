import storageDefault, * as storageNamed from "../storage";

const s = storageDefault || storageNamed || {};

const getAllMembers = async () => {
  try {
    const out =
      (await s.getAllMembers?.()) ??
      (await s.getAll?.("members")) ?? [];
    return Array.isArray(out) ? out : [];
  } catch (e) { console.error("[members.repo] getAllMembers", e); return []; }
};

const saveAllMembers = async (arr) => {
  try {
    if (s.saveMembers) return s.saveMembers(arr);
    if (s.saveAll)     return s.saveAll("members", arr);
    // Fallback: if only saveMember exists, write one by one
    if (s.saveMember)  {
      for (const m of arr) { /* eslint-disable no-await-in-loop */ await s.saveMember(m); }
      return;
    }
  } catch (e) { console.error("[members.repo] saveAllMembers", e); }
};

const pickId = (m) => m?.id ?? m?._id ?? m?.uuid;
const withId  = (m) => {
  const id = pickId(m) || (globalThis.crypto?.randomUUID?.() ?? String(Date.now()));
  // Keep original fields, but ensure a unified id for comparisons
  return { id, ...m };
};

export async function listMembers() {
  return (await getAllMembers()).map(withId);
}

export async function upsertMember(member) {
  const list = await listMembers();
  const norm = withId(member);
  const idx = list.findIndex(x => pickId(x) === pickId(norm));
  if (idx >= 0) list[idx] = { ...list[idx], ...norm };
  else list.push(norm);
  await saveAllMembers(list);
  return list;
}

export async function removeMember(idLike) {
  const list = await listMembers();
  const idStr = String(idLike);
  const next = list.filter(x => String(pickId(x)) !== idStr);
  await saveAllMembers(next);
  return next;
}

export default { listMembers, upsertMember, removeMember };