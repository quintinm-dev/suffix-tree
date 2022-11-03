"""Suffix tree via Ukkonen's algorithm as described by Gusfield."""

from __future__ import annotations
import sys
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt


class Node:
    """Nodes for a suffix tree."""

    next_id = 0

    @classmethod
    def create_root(cls) -> Node:
        root = Node()
        root.end = -1
        root.suffix_link = root
        root.parent = root

        return root

    @classmethod
    def reset_id(cls) -> None:
        cls.next_id = 0

    def __init__(
        self, start: int = None, end: int = None, parent: Node | None = None
    ) -> None:
        # Key is a starting index of edge into a child node
        self.children = {}

        # [start, end) defines the edge into this node
        self.start = start
        self.end = end

        self.parent = parent
        if parent:
            parent.children[start] = self

        # only defined for internal nodes
        self.suffix_link = None

        self.id = Node.next_id
        Node.next_id += 1

    def is_leaf(self) -> bool:
        return self.end is None


class SuffixTree:
    """Compressed suffix tree."""

    def __init__(self, word: str) -> None:
        global printing_disabled
        if printing_disabled:
            disable_printing()

        print(word)
        self.word = word

        Node.reset_id()
        self.root = Node.create_root()
        self._reset_active_point()

        self.first_leaf = None

        self.current_end = 0
        self.j_i = -1

    # Resets active point to given node, using root if none given
    def _reset_active_point(self, node: Node = None) -> None:
        # These three define the end of the current suffix
        self.active_node = node or self.root
        self.active_edge = None
        self.active_length = 0

    def build(self) -> None:
        for i in range(len(self.word)):
            self._phase(i - 1)
            print(f"done phase {i + 1}\n")
            self.print()

    # TODO: use termination char.
    # Currently returns true for prefixes of suffixes.
    def find(self, query: str) -> bool:
        curr_node = self.root
        query_idx = 0
        query_max = len(query)

        while query_idx < query_max:
            edge = self._find_edge(curr_node, query[query_idx])
            if edge is None:
                return False

            child = curr_node.children[edge]
            edge_length = self._node_length(child)

            walk_length = min(query_max - query_idx, edge_length)
            word_pos = edge
            for _ in range(walk_length):
                # We re-check the first character but that's fine
                if query[query_idx] != self.word[word_pos]:
                    return False

                query_idx += 1
                word_pos += 1

            curr_node = child

        return True

    # Phase i ensures all suffixes s[j..i+1] are present for 0 <= j <= i+1
    def _phase(self, i: int) -> None:
        self.prev_internal_node = None

        # First extension of phase i done in constant time.
        # Assumes active point is at the END of the last explicit extension
        # done in the previous phase.
        # Where explicit extension is the last extension where the end was
        # explicitly found, not the last rule 2 extension.
        print(
            f"phase start an: {self.active_node.id}, "
            f"ae: {self.active_edge}, al: {self.active_length}"
        )

        print(f"initial ensuring s[{self.j_i + 1}, {i + 1}] is in tree")

        rule_used = self._rule_extension(i)
        self._update_prev_internal_node(rule_used)
        self.print()

        if rule_used != "3":
            for j in range(self.j_i + 2, i + 2):
                rule_used = self._extend(j, i)
                if rule_used == "3":
                    self.j_i = j - 1
                    break

            if rule_used != "3":
                self.j_i = i

        # Have to do this prior to moving active point to s[i+1]
        # so that leaf edge lengths are correct
        self.current_end += 1

        # Make sure active point is at end, i.e. s[i+1] not s[i]
        if rule_used in ("2a", "2b"):
            self.active_node = self.active_node.children[i + 1]
        elif rule_used == "3":
            self.active_length += 1

            if self.active_length == 1:
                self.active_edge = self._find_edge(
                    self.active_node, self.word[i + 1]
                )

            child = self.active_node.children[self.active_edge]
            if self.active_length == self._node_length(child):
                self._reset_active_point(child)

    # old extension logic:
    # if j == 0:
    #     self._reset_active_point(self.first_leaf)
    #     rule_used = self._rule_extension(i)
    # else:

    # Extension j ensures suffix s[j..i+1] is in the tree
    def _extend(self, j: int, i: int) -> None:
        print(f"ensuring s[{j}, {i + 1}] is in tree")

        rule_used = self._single_extension_algorithm(j, i)

        self.print()

        return rule_used

    # Walks from start_node over s[start, end) which must already be in the tree
    def _walk(self, start: int, end: int, start_node: Node) -> None:
        self._reset_active_point(start_node)

        if start == end:
            return

        curr = start

        while True:
            c = self.word[curr]
            edge = self._find_edge(self.active_node, c)
            child = self.active_node.children[edge]
            edge_length = self._node_length(child)

            remaining_walk_length = end - curr

            if edge_length < remaining_walk_length:
                self.active_node = child
                curr += edge_length
            elif edge_length == remaining_walk_length:
                self.active_node = child
                break
            else:
                self.active_length = remaining_walk_length
                self.active_edge = edge
                break

    # Handles extending the current suffix with s[i+1]
    # Returns rule used, one of '1', '2a' (no split), '2b' (split), '3'
    # Moves the active point to the internal node if there's a split
    def _rule_extension(self, i: int) -> str:
        # Rule 1: ends at leaf node, extend path
        if self.active_length == 0 and self.active_node.is_leaf():
            print("Rule 1")
            # Extension is implicit
            # Technically this leaves the active point at s[i+1] instead of s[i]
            # but I think that's OK, as leaves should never have links,
            # and the parent of this will always have a link if it's internal
            return "1"

        c = self.word[i + 1]

        # Rule 2: no existing path
        if (
            self.active_edge is None
            and self._find_edge(self.active_node, c) is None
        ):
            child = Node(start=i + 1, parent=self.active_node)

            if not self.first_leaf:
                self.first_leaf = child

            print("Rule 2")
            return "2a"
        elif (
            self.active_edge is not None
            and c != self.word[self.active_edge + self.active_length]
        ):
            prev_child = self.active_node.children.pop(self.active_edge)
            prev_child.start = prev_child.start + self.active_length

            internal_node = Node(
                start=self.active_edge,
                end=prev_child.start,
                parent=self.active_node,
            )

            internal_node.children[prev_child.start] = prev_child
            prev_child.parent = internal_node

            internal_node.children[i + 1] = Node(
                start=i + 1, parent=internal_node
            )

            # Need to make sure the active point is updated given the split
            self._reset_active_point(internal_node)

            print("Rule 2 split")
            return "2b"

        # Rule 3: implicit suffix, already in tree
        print("Rule 3")
        return "3"

    def _update_prev_internal_node(self, rule_used: str) -> None:
        if rule_used == "2b":
            self.prev_internal_node = self.active_node
        else:
            self.prev_internal_node = None

    # Returns whatever _rule_extension(i) returns
    def _single_extension_algorithm(self, j: int, i: int) -> str:
        print(
            f"prewalk an: {self.active_node.id}, "
            f"ae: {self.active_edge}, al: {self.active_length}"
        )

        # TODO: refactor this spaghetti
        if self.active_node == self.root:
            self._walk(j, i + 1, self.root)
        else:
            # gamma is the string between the active_node and end of S[j-1..i]
            # that we need to re-traverse after moving to v's suffix link
            if self.active_length == 0 and self.active_node.suffix_link is None:
                # handle walking up from a node rather than an edge
                child = self.active_node

                if child.parent == self.root:
                    self._walk(j, i + 1, self.root)
                else:
                    # need to use length offset for end in case child is a leaf
                    gamma_indexes = (
                        child.start,
                        child.start + self._node_length(child),
                    )
                    if not child.parent.suffix_link:
                        raise AssertionError("uhoh")

                    self._walk(*gamma_indexes, child.parent.suffix_link)
            else:
                if self.active_edge is None:
                    # empty gamma
                    gamma_indexes = (-1, -1)
                else:
                    gamma_indexes = (
                        self.active_edge,
                        self.active_edge + self.active_length,
                    )
                self._walk(*gamma_indexes, self.active_node.suffix_link)

        print(
            f"postwalk an: {self.active_node.id}, "
            f"ae: {self.active_edge}, al: {self.active_length}"
        )

        prev_internal_node = self.prev_internal_node

        rule_used = self._rule_extension(i)
        self._update_prev_internal_node(rule_used)

        # Suffix link update has to happen after extension,
        # as node for end of s[j..i] does not necessarily exist until
        # we insert s[i+1], i.e. when it's a case 2 split
        if prev_internal_node:
            prev_internal_node.suffix_link = self.active_node

        return rule_used

    def _node_length(self, node: Node) -> int:
        end = self.current_end if node.is_leaf() else node.end
        return end - node.start

    def _find_edge(self, node: Node, char: str) -> bool:
        # Could hold chars in a dict but this is already O(1)
        for i in node.children.keys():
            if char == self.word[i]:
                return i

        return None

    def print(self, force=False):
        global printing_disabled
        if printing_disabled and not force:
            return

        G = nx.DiGraph()  # pylint: disable=invalid-name
        G.add_nodes_from(range(Node.next_id))

        # DFS tree traversal (pre-order but doesn't really matter)
        todo = [self.root]
        while todo:
            curr = todo.pop()

            if curr.suffix_link:
                G.add_edge(curr.id, curr.suffix_link.id, is_suffix=True)

            for child in curr.children.values():
                substr = self.word[child.start : child.end or self.current_end]
                G.add_edge(curr.id, child.id, label=substr, is_suffix=False)

                todo.append(child)

        # Make graphviz layout left to right
        G.graph["graph"] = dict(rankdir="LR")

        # Tree layout
        pos = graphviz_layout(G, prog="dot")

        is_edge_suffix = nx.get_edge_attributes(G, "is_suffix")
        suffix_links, edges = [], []
        for e in G.edges():
            if is_edge_suffix[e]:
                suffix_links.append(e)
            else:
                edges.append(e)

        plt.figure()
        # Draw nodes + edges
        nx.draw(
            G,
            pos,
            linewidths=1,
            node_size=1000,
            node_color="pink",
            alpha=0.9,
            edgelist=edges,
            edge_color="b",
            width=2,
            with_labels=True,
            arrows=True,
            arrowsize=20,
        )
        # Draw suffix links
        nx.draw_networkx_edges(
            G,
            pos,
            node_size=1000,
            edgelist=suffix_links,
            edge_color="m",
            width=1,
            style="dashed",
            connectionstyle="arc3, rad = 0.1",
            arrows=True,
            arrowsize=20,
        )
        nx.draw_networkx_edge_labels(
            G, pos, font_size=16, edge_labels=nx.get_edge_attributes(G, "label")
        )

        plt.axis("off")
        plt.show()


# Kind of silly, should just use logging library but I want to disable plots too
printing_disabled = True


def disable_printing():
    global print

    def print(*_):
        return


def main():
    if len(sys.argv) > 2 and sys.argv[2] == "-v":
        global printing_disabled
        printing_disabled = False

    word = sys.argv[1]
    tree = SuffixTree(word)
    tree.build()
    tree.print(force=True)


if __name__ == "__main__":
    main()
