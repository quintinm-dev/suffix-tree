"""Suffix tree via Ukkonen's algorithm as described by Gusfield."""

import sys
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt


class Node:
    """Nodes for a suffix tree."""

    next_id = 0

    @classmethod
    def create_root(cls) -> "Node":
        root = Node()
        root.end = -1

        return root

    @classmethod
    def reset_id(cls) -> None:
        cls.next_id = 0

    def __init__(self, start: int = None) -> None:
        # Key is a starting index of edge into a child node
        self.children = {}

        # [start, end) defines the edge into this node
        self.start = start
        self.end = None

        # only defined for internal nodes
        self.suffix_link = None

        self.id = Node.next_id
        Node.next_id += 1

    def is_leaf(self) -> bool:
        return self.end is None


class SuffixTree:
    """Compressed suffix tree."""

    def __init__(self, word: str) -> None:
        self.word = word

        Node.reset_id()
        self.root = Node.create_root()
        self._reset_active_point()

        self.first_leaf = None

        self.current_end = 0

    # Resets active point to given node, using root if none given
    def _reset_active_point(self, node: "Node" = None) -> None:
        # These three define the end of the current suffix
        self.active_node = node or self.root
        self.active_edge = None
        self.active_length = 0

    def build(self) -> None:
        for i in range(len(self.word)):
            self._phase(i - 1)
            self.current_end += 1

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
        for j in range(0, i + 2):
            self._extend(j, i)

    # Extension j ensures suffix s[j..i+1] is in the tree
    def _extend(self, j: int, i: int) -> None:
        print(f"ensuring s[{j}, {i + 1}] is in tree")

        if j == 0:
            self._reset_active_point(self.first_leaf)
        else:
            self._walk(j, i + 1, self.root)

        print(
            f"postwalk an: {self.active_node.id}, "
            f"ae: {self.active_edge}, al: {self.active_length}"
        )

        self._rule_extension(i)

    # Walks from start_node over s[start, end) which must already be in the tree
    def _walk(self, start: int, end: int, start_node: "Node") -> None:
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
    def _rule_extension(self, i: int) -> None:
        # Rule 1: ends at leaf node, extend path
        if self.active_length == 0 and self.active_node.is_leaf():
            print("Rule 1")
            # Extension is implicit
            return None

        c = self.word[i + 1]

        # Rule 2: no existing path
        if (
            self.active_edge is None
            and self._find_edge(self.active_node, c) is None
        ):
            child = Node(start=i + 1)
            self.active_node.children[i + 1] = child

            if not self.first_leaf:
                self.first_leaf = child

            print("Rule 2")
            return None
        elif (
            self.active_edge is not None
            and c != self.word[self.active_edge + self.active_length]
        ):
            prev_child = self.active_node.children.pop(self.active_edge)
            prev_child.start = prev_child.start + self.active_length

            internal_node = Node(start=self.active_edge)
            internal_node.start = self.active_edge
            internal_node.end = prev_child.start

            internal_node.children[prev_child.start] = prev_child
            internal_node.children[i + 1] = Node(start=i + 1)

            self.active_node.children[self.active_edge] = internal_node

            print("Rule 2 split")
            return None
        # TODO: handle suffix links

        # Rule 3: implicit suffix, already in tree
        print("Rule 3")
        return None

    def _node_length(self, node: "Node") -> int:
        end = self.current_end if node.is_leaf() else node.end
        return end - node.start

    def _find_edge(self, node: "Node", char: str) -> bool:
        # Could hold chars in a dict but this is already O(1)
        for i in node.children.keys():
            if char == self.word[i]:
                return i

        return None

    def print(self):
        G = nx.DiGraph()  # pylint: disable=invalid-name
        G.add_nodes_from(range(Node.next_id))

        # DFS tree traversal (pre-order but doesn't really matter)
        todo = [self.root]
        while todo:
            curr = todo.pop()

            # if curr.suffix_link:
            #     G.add_edge(curr.id, curr.suffix_link.id, weight=1, color='m')

            for child in curr.children.values():
                # substr = f"[{child.start}, {child.end or self.current_end})"
                substr = self.word[child.start : child.end or self.current_end]
                G.add_edge(curr.id, child.id, label=substr, weight=2, color="b")

                todo.append(child)

        # Make graphviz layout left to right
        G.graph["graph"] = dict(rankdir="LR")

        # Tree layout
        pos = graphviz_layout(G, prog="dot")

        plt.figure()
        nx.draw(
            G,
            pos,
            linewidths=1,
            node_size=1000,
            node_color="pink",
            alpha=0.9,
            edge_color=nx.get_edge_attributes(G, "color").values(),
            width=list(nx.get_edge_attributes(G, "weight").values()),
            with_labels=True,
            arrows=True,
        )
        nx.draw_networkx_edge_labels(
            G, pos, font_size=16, edge_labels=nx.get_edge_attributes(G, "label")
        )

        print(f"first leaf: {self.first_leaf and self.first_leaf.id}")

        plt.axis("off")
        plt.show()


def main():
    word = sys.argv[1]
    tree = SuffixTree(word)
    tree.build()
    tree.print()


if __name__ == "__main__":
    main()
