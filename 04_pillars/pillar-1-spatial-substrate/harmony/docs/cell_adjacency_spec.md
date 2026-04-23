# Harmony Spatial Operating System — Pillar I — Spatial Substrate
# Cell Adjacency Specification

> **Version:** 1.0  
> **Status:** Accepted  
> **Date:** April 2026  
> **Scope:** Defines the adjacency model for the Harmony Cell System — intra-face neighbours, inter-face boundary transitions, vertex adjacency, adjacency rings, and resolution boundary behaviour.  
> **Governing Documents:** cell_geometry_spec.md, cell_key_derivation_spec.md, ADR-003-cell-key-derivation.md  
> **Motivation:** Predictive LOD rendering requires the renderer to know not only which child cells to load (zoom — parent-child hierarchy) but also which lateral cells to load (movement — adjacency). Without a formal adjacency model, the rendering engine cannot prefetch tiles in the direction of camera or entity movement.

---

## 1. Definitions

### 1.1 Cell Address Tuple

Every cell in the Harmony Cell System is uniquely identified by a **cell address tuple**:

```
(face, resolution, i, j)
```

where:

- `face` is the cube face index, 0–5 (see cell_geometry_spec.md §5.1)
- `resolution` is the resolution level, 0–12
- `i` is the column index within the face grid, 0 ≤ i < N where N = 4^resolution
- `j` is the row index within the face grid, 0 ≤ j < N

The cell address tuple and the cell_key are two representations of the same cell. The cell address tuple is used for adjacency computation (grid arithmetic). The cell_key is used for identity and storage. Conversion between the two is deterministic.

### 1.2 Adjacency Types

**Edge adjacency:** Two cells are edge-adjacent if they share a complete grid edge. Every interior cell has exactly 4 edge-adjacent neighbours: +u, -u, +v, -v (right, left, up, down in the UV grid). Boundary cells have some edge neighbours on adjacent cube faces.

**Vertex adjacency:** Two cells are vertex-adjacent if they share a grid vertex but not a grid edge. Every interior cell has exactly 4 vertex-adjacent neighbours: (+u,+v), (+u,-v), (-u,+v), (-u,-v) (the diagonals). Boundary and corner cells have vertex neighbours that may span cube faces.

**Full adjacency:** The union of edge and vertex adjacency. Every interior cell has exactly 8 full-adjacent neighbours.

### 1.3 Adjacency Ring

An **adjacency ring of order k** around a cell C is the set of all cells whose Chebyshev distance from C on the grid is exactly k. The ring of order 1 is the set of 8 fully-adjacent neighbours. For cells near face boundaries, the ring may span multiple cube faces.

The ring of order k contains at most 8k cells (the perimeter of a (2k+1) × (2k+1) square minus the (2k-1) × (2k-1) interior).

---

## 2. Intra-Face Adjacency

### 2.1 Edge Neighbours (Same Face)

For a cell at `(face, r, i, j)` where N = 4^r:

| Direction | Neighbour (i', j') | Condition |
|-----------|-------------------|-----------|
| +u (right) | (i+1, j) | i < N-1 |
| -u (left) | (i-1, j) | i > 0 |
| +v (up) | (i, j+1) | j < N-1 |
| -v (down) | (i, j-1) | j > 0 |

If the condition is not met, the neighbour is on an adjacent cube face (see §3).

### 2.2 Vertex Neighbours (Same Face)

| Direction | Neighbour (i', j') | Condition |
|-----------|-------------------|-----------|
| (+u, +v) | (i+1, j+1) | i < N-1 and j < N-1 |
| (+u, -v) | (i+1, j-1) | i < N-1 and j > 0 |
| (-u, +v) | (i-1, j+1) | i > 0 and j < N-1 |
| (-u, -v) | (i-1, j-1) | i > 0 and j > 0 |

If either coordinate falls outside the grid, the vertex neighbour requires inter-face resolution. Cells at cube face corners require special handling because the diagonal neighbour is on a third face (see §3.3).

---

## 3. Inter-Face Adjacency

### 3.1 Cube Face Topology

The six cube faces share 12 edges. Each edge is shared by exactly two faces. The adjacency relationships are determined by the cube geometry and the UV mapping defined in cell_geometry_spec.md §5.1.

Recall the UV mapping:

| Face | Name | UV Mapping |
|------|------|------------|
| 0 | +X | u = y/\|x\|, v = z/\|x\| |
| 1 | -X | u = y/\|x\|, v = z/\|x\| |
| 2 | +Y | u = x/\|y\|, v = z/\|y\| |
| 3 | -Y | u = x/\|y\|, v = z/\|y\| |
| 4 | +Z | u = x/\|z\|, v = y/\|z\| |
| 5 | -Z | u = x/\|z\|, v = y/\|z\| |

### 3.2 Boundary Transition Table

The following table defines all 24 directed boundary transitions (12 cube edges × 2 directions). For a cell at grid position (i, j) on the source face that lies on the specified edge, the table gives the neighbour's face and grid position (i', j'). Let N = 4^r - 1 (maximum grid index at resolution r).

**Face 0 (+X) Boundary Transitions:**

| Source Edge | Source Constraint | Dest Face | i' | j' |
|-------------|-------------------|-----------|-----|-----|
| u = +1 | i = N | 2 (+Y) | N | j |
| u = -1 | i = 0 | 3 (-Y) | N | j |
| v = +1 | j = N | 4 (+Z) | N | i |
| v = -1 | j = 0 | 5 (-Z) | N | i |

**Face 1 (-X) Boundary Transitions:**

| Source Edge | Source Constraint | Dest Face | i' | j' |
|-------------|-------------------|-----------|-----|-----|
| u = +1 | i = N | 2 (+Y) | 0 | j |
| u = -1 | i = 0 | 3 (-Y) | 0 | j |
| v = +1 | j = N | 4 (+Z) | 0 | i |
| v = -1 | j = 0 | 5 (-Z) | 0 | i |

**Face 2 (+Y) Boundary Transitions:**

| Source Edge | Source Constraint | Dest Face | i' | j' |
|-------------|-------------------|-----------|-----|-----|
| u = +1 | i = N | 0 (+X) | N | j |
| u = -1 | i = 0 | 1 (-X) | N | j |
| v = +1 | j = N | 4 (+Z) | i | N |
| v = -1 | j = 0 | 5 (-Z) | i | N |

**Face 3 (-Y) Boundary Transitions:**

| Source Edge | Source Constraint | Dest Face | i' | j' |
|-------------|-------------------|-----------|-----|-----|
| u = +1 | i = N | 0 (+X) | 0 | j |
| u = -1 | i = 0 | 1 (-X) | 0 | j |
| v = +1 | j = N | 4 (+Z) | i | 0 |
| v = -1 | j = 0 | 5 (-Z) | i | 0 |

**Face 4 (+Z) Boundary Transitions:**

| Source Edge | Source Constraint | Dest Face | i' | j' |
|-------------|-------------------|-----------|-----|-----|
| u = +1 | i = N | 0 (+X) | j | N |
| u = -1 | i = 0 | 1 (-X) | j | N |
| v = +1 | j = N | 2 (+Y) | i | N |
| v = -1 | j = 0 | 3 (-Y) | i | N |

**Face 5 (-Z) Boundary Transitions:**

| Source Edge | Source Constraint | Dest Face | i' | j' |
|-------------|-------------------|-----------|-----|-----|
| u = +1 | i = N | 0 (+X) | j | 0 |
| u = -1 | i = 0 | 1 (-X) | j | 0 |
| v = +1 | j = N | 2 (+Y) | i | 0 |
| v = -1 | j = 0 | 3 (-Y) | i | 0 |

### 3.2.1 Derivation of the Boundary Transition Table

Each entry in the table is derived from the UV mapping in cell_geometry_spec.md §5.1. The procedure for a given (source_face, edge) pair:

1. Identify the 3D cube edge shared by source_face and the destination face. For example, Face 0 (+X) at u=+1 means y = x (both positive) on the unit cube, which is the shared edge with Face 2 (+Y).

2. Express the destination face's UV coordinates in terms of the source face's UV coordinates at the shared edge. Use the identity that at the shared boundary, the dominant axes of both faces have equal magnitude.

3. Map the source cell's grid position to the destination face's grid position using the UV coordinate relationship.

**Example — Face 0, u=+1 → Face 2:**

On Face 0, u₀ = y/|x| and v₀ = z/|x|. At u₀ = +1, y = x (both positive). The point enters Face 2 (+Y), where u₂ = x/|y| and v₂ = z/|y|. At the boundary x = y, so u₂ = x/y = 1 and v₂ = z/y = z/x = v₀. The destination cell is at the u₂ = +1 edge (i' = N) with the same v-position (j' = j).

**Example — Face 4, u=+1 → Face 0:**

On Face 4, u₄ = x/|z| and v₄ = y/|z|. At u₄ = +1, x = z. The point enters Face 0 (+X), where u₀ = y/|x| and v₀ = z/|x|. At the boundary x = z, so u₀ = y/x = y/z = v₄ and v₀ = z/x = 1. The destination cell is at v₀ = +1 (j' = N) with i' mapping to v₄, meaning i' = j_source.

### 3.2.2 Symmetry Verification

Every transition has a corresponding reverse transition. The table is self-consistent:

| Forward | Reverse | Verification |
|---------|---------|-------------|
| Face 0 u=+1 → Face 2 (N, j) | Face 2 u=+1 → Face 0 (N, j) | ✓ Mutual at i=N, j preserved |
| Face 0 u=-1 → Face 3 (N, j) | Face 3 u=+1 → Face 0 (0, j) | ✓ Face 0 i=0 ↔ Face 3 i=N |
| Face 0 v=+1 → Face 4 (N, i) | Face 4 u=+1 → Face 0 (j, N) | ✓ With j_src=i_Face0, i_Face4=N |
| Face 0 v=-1 → Face 5 (N, i) | Face 5 u=+1 → Face 0 (j, 0) | ✓ With j_src=i_Face0, i_Face5=N |
| Face 1 u=+1 → Face 2 (0, j) | Face 2 u=-1 → Face 1 (N, j) | ✓ Face 1 i=N ↔ Face 2 i=0 |
| Face 1 u=-1 → Face 3 (0, j) | Face 3 u=-1 → Face 1 (0, j) | ✓ Mutual at i=0, j preserved |
| Face 1 v=+1 → Face 4 (0, i) | Face 4 u=-1 → Face 1 (j, N) | ✓ With j_src=i_Face1, i_Face4=0 |
| Face 1 v=-1 → Face 5 (0, i) | Face 5 u=-1 → Face 1 (j, 0) | ✓ With j_src=i_Face1, i_Face5=0 |
| Face 2 v=+1 → Face 4 (i, N) | Face 4 v=+1 → Face 2 (i, N) | ✓ Mutual at j=N, i preserved |
| Face 2 v=-1 → Face 5 (i, N) | Face 5 v=+1 → Face 2 (i, 0) | ✓ Face 2 j=0 ↔ Face 5 j=N→i mapped |
| Face 3 v=+1 → Face 4 (i, 0) | Face 4 v=-1 → Face 3 (i, N) | ✓ Face 3 j=N ↔ Face 4 j=0 |
| Face 3 v=-1 → Face 5 (i, 0) | Face 5 v=-1 → Face 3 (i, 0) | ✓ Mutual at j=0, i preserved |

All 12 undirected edge adjacencies are verified as symmetric.

### 3.3 Cube Corner Adjacency

A cube has 8 corners. Each corner is shared by exactly 3 faces. A cell at a cube corner has two edge neighbours on adjacent faces (one per boundary edge) and one vertex (diagonal) neighbour on the third face sharing that corner.

The 8 cube corners and their 3 adjacent faces:

| Corner (x, y, z) | Face A | Face B | Face C |
|-------------------|--------|--------|--------|
| (+1, +1, +1) | 0 (+X) | 2 (+Y) | 4 (+Z) |
| (+1, +1, -1) | 0 (+X) | 2 (+Y) | 5 (-Z) |
| (+1, -1, +1) | 0 (+X) | 3 (-Y) | 4 (+Z) |
| (+1, -1, -1) | 0 (+X) | 3 (-Y) | 5 (-Z) |
| (-1, +1, +1) | 1 (-X) | 2 (+Y) | 4 (+Z) |
| (-1, +1, -1) | 1 (-X) | 2 (+Y) | 5 (-Z) |
| (-1, -1, +1) | 1 (-X) | 3 (-Y) | 4 (+Z) |
| (-1, -1, -1) | 1 (-X) | 3 (-Y) | 5 (-Z) |

Due to the tie-breaking rule (X > Y > Z), the cube corner is assigned to one face deterministically. The corner cell on the assigned face has its diagonal neighbour on the third face (not the edge-neighbour faces).

**Example — Corner (+1, +1, +1):**

By tie-breaking (X wins ties), |x| ≥ |y| ≥ |z| so the point is assigned to Face 0 (+X). On Face 0, the corner cell is at (i=N, j=N). Its +u edge neighbour is on Face 2 at (N, N). Its +v edge neighbour is on Face 4 at (N, N). Its (+u, +v) diagonal neighbour is the cell at the same corner on the third face visible from that corner. Following the boundary transitions:

- From Face 0 (N, N) going +u → Face 2 (N, N). From Face 2 (N, N) going +v → Face 4 (N, N).
- The diagonal neighbour at the corner is therefore Face 4 at (N, N), which is the same cell reached by the two-step path through any intermediate face.

At resolution 0 (N=0), all three corner-sharing faces have a single cell each, and all three are mutual neighbours.

### 3.4 Vertex Neighbour Algorithm for Boundary Cells

To find the vertex neighbour at direction (du, dv) for a boundary cell:

```
function vertex_neighbour(face, r, i, j, du, dv):
    N = 4^r - 1
    i_new = i + du
    j_new = j + dv

    if 0 <= i_new <= N and 0 <= j_new <= N:
        return (face, i_new, j_new)    # intra-face case

    # Resolve each overflowing axis independently via the boundary table
    if i_new < 0 or i_new > N:
        (face_u, i_u, j_u) = boundary_transition(face, 'u', sign(du), i, j)
    else:
        (face_u, i_u, j_u) = (face, i_new, j)

    if j_new < 0 or j_new > N:
        (face_v, i_v, j_v) = boundary_transition(face, 'v', sign(dv), i, j)
    else:
        (face_v, i_v, j_v) = (face, i, j_new)

    # If both axes overflow (corner case), resolve via two-step transition
    if (i_new < 0 or i_new > N) and (j_new < 0 or j_new > N):
        # Step 1: cross one face boundary
        (mid_face, mid_i, mid_j) = boundary_transition(face, 'u', sign(du), i, j)
        # Step 2: from the mid-face, resolve the v-direction overflow
        # The v-direction on the source face may map to a different axis
        # on the mid-face. Use the coordinate mapping from §3.2 to determine
        # which axis on mid_face corresponds to the source's v-axis.
        return resolve_corner_diagonal(face, mid_face, mid_i, mid_j, dv)

    # If only one axis overflows, combine the resolved face with the
    # in-bounds coordinate from the other axis, applying the appropriate
    # coordinate transformation.
    if i_new < 0 or i_new > N:
        return apply_cross_face_offset(face_u, i_u, j_u, 'v', dv)
    else:
        return apply_cross_face_offset(face_v, i_v, j_v, 'u', du)
```

The full implementation of `resolve_corner_diagonal` and `apply_cross_face_offset` is provided in the adjacency module (Deliverable 4, Session 3 or later). The principle is: resolve the corner diagonal by stepping through an intermediate face, applying the coordinate transformations from §3.2 at each step.

---

## 4. Adjacency Ring Computation

### 4.1 Definition

The adjacency ring of order k around cell C at `(face, r, i, j)` is:

```
Ring(C, k) = { cell D : max(|i_D - i_C|, |j_D - j_C|) = k }
```

where the distance computation accounts for inter-face coordinate transformations when cells span face boundaries.

For cells whose ring does not cross a face boundary, this is the set of cells forming the perimeter of a (2k+1) × (2k+1) square centred on C, containing exactly 8k cells.

### 4.2 Practical Scope

For predictive LOD rendering, only rings of order 1 through 3 are needed:

| Ring Order | Cell Count (max) | Purpose |
|------------|-----------------|---------|
| 1 | 8 | Immediate neighbours — minimum for movement prediction |
| 2 | 16 | Extended neighbourhood — smooth LOD transitions |
| 3 | 24 | Prefetch horizon — aggressive movement prediction |

The adjacency model is defined for arbitrary k but the implementation is optimised for k ≤ 3.

### 4.3 Ring Computation Algorithm

```
function adjacency_ring(face, r, i, j, k):
    ring = []
    for di in range(-k, k+1):
        for dj in range(-k, k+1):
            if max(abs(di), abs(dj)) != k:
                continue
            (dest_face, dest_i, dest_j) = resolve_neighbour(face, r, i, j, di, dj)
            ring.append((dest_face, r, dest_i, dest_j))
    return ring
```

The `resolve_neighbour` function handles intra-face, edge-crossing, and corner-crossing cases using the boundary transition table from §3.2.

### 4.4 Cross-Face Ring Cells

When a ring extends beyond a face boundary, the cells on the other face are included. A ring of order 1 can span at most 2 faces (edge crossing) or 3 faces (corner crossing). A ring of order k can span up to 3 faces for cells near a corner.

The coordinate transformation is applied per-cell using the boundary transition table. There is no approximation or clipping at face boundaries.

---

## 5. Resolution Boundary Behaviour

### 5.1 Same-Resolution Adjacency

All adjacency definitions in this specification operate within a single resolution level. The neighbours of a Level 8 cell are other Level 8 cells. Adjacency does not cross resolution levels.

### 5.2 Parent-Child Relationship (Vertical Adjacency)

Parent-child relationships are defined in cell_geometry_spec.md §3.4. A cell at `(face, r, i, j)` has 16 children at level r+1 at positions `(face, r+1, 4i+di, 4j+dj)` for di, dj ∈ {0, 1, 2, 3}. Its parent is at `(face, r-1, floor(i/4), floor(j/4))`.

Parent-child relationships are hierarchical (vertical), not lateral. They are complementary to the adjacency model defined here.

### 5.3 Cross-Resolution Neighbour Mapping

Given a cell C at resolution r and a neighbour N at the same resolution, the children of N that are adjacent to the children of C can be determined by combining the parent-child containment rule with the adjacency grid positions. This is used by the LOD engine when transitioning between resolution levels at cell boundaries.

Specifically, if C is at `(f, r, i, j)` and N is the +u edge neighbour at `(f', r, i', j')`, then the children of C along the +u edge (those with di=3) are adjacent to the children of N along the -u edge (those with di=0):

```
C's +u edge children: (f, r+1, 4i+3, 4j+dj) for dj ∈ {0,1,2,3}
N's -u edge children: (f', r+1, 4i'+0, 4j'+dj) for dj ∈ {0,1,2,3}
```

Each child pair shares an edge if their j-coordinates correspond (accounting for the boundary transition if f ≠ f').

---

## 6. Stored Adjacency

### 6.1 What Is Stored

Each cell record in the Identity Registry stores its edge-adjacent neighbours as an array of cell_keys:

```
adjacent_cell_keys: TEXT[]   -- 4 entries for edge adjacency, ordered [+u, -u, +v, -v]
```

This array contains exactly 4 cell_keys, one per edge direction. The order is fixed: index 0 = +u, index 1 = -u, index 2 = +v, index 3 = -v.

### 6.2 What Is Computed at Runtime

Vertex adjacency (diagonal neighbours) and adjacency rings of order > 1 are computed at runtime from the stored edge adjacency using the algorithms in §2, §3, and §4. Storing all 8 neighbours or larger rings would introduce redundancy and maintenance burden without significant performance benefit, since the boundary transition table is O(1).

### 6.3 Null Adjacency

At resolution level 0, each face has one cell. That cell's edge neighbours are the 4 adjacent face cells. All 4 entries in `adjacent_cell_keys` are populated — there is no resolution level at which adjacency is undefined.

---

## 7. Adjacency Invariants

The following invariants must hold for any correct implementation:

1. **Symmetry.** If cell A is the +u neighbour of cell B, then cell B is one of cell A's edge neighbours (though not necessarily in the -u direction, due to coordinate axis remapping across face boundaries).

2. **Completeness.** Every cell at every resolution level has exactly 4 edge neighbours. There are no orphan cells.

3. **Determinism.** The adjacency of a cell is fully determined by its cell address tuple `(face, r, i, j)`. No database lookup is required to compute adjacency — only the boundary transition table.

4. **Consistency with cell_key.** The cell_key of a neighbour computed via the boundary transition table must match the cell_key obtained by deriving from the neighbour's centroid coordinates. This is the canonical correctness test.

5. **Parent-child alignment.** If cell A and cell B are edge-adjacent at resolution r, then their parents at resolution r-1 are either the same cell or are themselves edge-adjacent (or vertex-adjacent in the case of diagonal parent relationships).

---

## 8. Implementation Notes

### 8.1 Boundary Transition Table as Code

The boundary transition table (§3.2) should be implemented as a static lookup structure, not computed dynamically. The table has 24 entries (6 faces × 4 edges) and each entry is a simple coordinate mapping function. A suggested implementation is an array of tuples:

```python
# (dest_face, i_func, j_func)
# where i_func and j_func are one of:
#   'i' -> source i
#   'j' -> source j
#   'N' -> N (max grid index)
#   '0' -> 0
BOUNDARY_TABLE = {
    (0, '+u'): (2, 'N', 'j'),
    (0, '-u'): (3, 'N', 'j'),
    (0, '+v'): (4, 'N', 'i'),
    (0, '-v'): (5, 'N', 'i'),
    (1, '+u'): (2, '0', 'j'),
    (1, '-u'): (3, '0', 'j'),
    (1, '+v'): (4, '0', 'i'),
    (1, '-v'): (5, '0', 'i'),
    (2, '+u'): (0, 'N', 'j'),
    (2, '-u'): (1, 'N', 'j'),
    (2, '+v'): (4, 'i', 'N'),
    (2, '-v'): (5, 'i', 'N'),
    (3, '+u'): (0, '0', 'j'),
    (3, '-u'): (1, '0', 'j'),
    (3, '+v'): (4, 'i', '0'),
    (3, '-v'): (5, 'i', '0'),
    (4, '+u'): (0, 'j', 'N'),
    (4, '-u'): (1, 'j', 'N'),
    (4, '+v'): (2, 'i', 'N'),
    (4, '-v'): (3, 'i', 'N'),
    (5, '+u'): (0, 'j', '0'),
    (5, '-u'): (1, 'j', '0'),
    (5, '+v'): (2, 'i', '0'),
    (5, '-v'): (3, 'i', '0'),
}
```

### 8.2 Performance

Edge neighbour lookup is O(1) — a table lookup plus at most one coordinate swap. Adjacency ring computation is O(k) where k is the ring order. No trigonometry, no projection, no hashing is required for adjacency computation itself.

For the common case of movement prediction (ring order 1), the total cost is 8 table lookups plus 8 cell_key derivations (for the rendering engine to identify the tiles to fetch).

### 8.3 Testing Strategy

The adjacency implementation must be tested against the following:

1. **Intra-face round-trip:** For every cell at a test resolution, verify that the +u neighbour's -u neighbour is the original cell (accounting for axis remapping at face boundaries).

2. **Inter-face consistency:** For boundary cells, verify that the neighbour cell_key computed via the boundary transition table matches the cell_key derived from the neighbour's centroid coordinates.

3. **Cube corner coverage:** For all 8 cube corners, verify that the three face cells sharing the corner are mutually reachable via the adjacency model.

4. **Ring completeness:** For sample cells, verify that the adjacency ring of order k contains exactly 8k cells (or fewer only at cube corners where faces meet).

5. **Symmetry:** For a random sample of cells, verify that if A is in the neighbours of B, then B is in the neighbours of A.

---

*End of Cell Adjacency Specification*
