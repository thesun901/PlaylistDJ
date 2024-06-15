import processing_functions
from spotify_setup import sp
import math

class Track:
    def __init__(self, song: dict):
        self.id: str = song['id']
        self.uri = song['uri']
        self.name = song['name']
        features = processing_functions.get_audio_features(self.id)
        self.loudness = features['loudness']
        self.energy = features['energy']
        self.instrumentalness = features['instrumentalness']
        self.tempo = features['tempo']
        self.valence = features['valence']
        self.danceability = features['danceability']


class Playlist:
    def __init__(self, playlist_dict: dict):
        self.id: str = playlist_dict['id']
        self.name: str = playlist_dict['name']
        self.image: str = playlist_dict['images'][0]['url']
        self.tracklist = []
        playlist_tracks = processing_functions.get_all_tracks(self.id)
        for item in playlist_tracks:
            self.tracklist.append(Track(item['track']))


class TrackNode:
    def __init__(self, track: Track):
        self.track = track
        self.loudness_dimention = 0
        self.energy_dimention = 0
        self.instrumentalness_dimention = 0
        self.tempo_dimention = 0
        self.valence_dimention = 0
        self.danceability_dimention = 0

        self.neighbours: set[TrackNode] = set()


class TracksGraph:
    def __init__(self, playlist: Playlist):
        self.nodes = []
        self._normalize_features(playlist.tracklist)

        self.loudness_relevant = True
        self.energy_relevant = True
        self.instrumentalness_relevant = False
        self.tempo_relevant = True
        self.valence_relevant = False
        self.danceability_relevant = False

        self.build_graph()

    def _normalize_features(self, tracks):
        # loudnes feature has only negative values
        max_loudness = float('-inf')
        max_energy = 0
        max_instrumentalness = 0
        max_tempo = 0
        max_valence = 0
        max_danceability = 0

        for track in tracks:
            if track.loudness > max_loudness:
                max_loudness = track.loudness
            if track.energy > max_energy:
                max_energy = track.energy
            if track.instrumentalness > max_instrumentalness:
                max_instrumentalness = track.instrumentalness
            if track.tempo > max_tempo:
                max_tempo = track.tempo
            if track.valence > max_valence:
                max_valence = track.valence
            if track.danceability > max_danceability:
                max_danceability = track.danceability

        for track in tracks:
            node = TrackNode(track)
            node.loudness_dimention = (track.loudness - max_loudness) / -max_loudness  # normalize negative value
            node.energy_dimention = track.energy / max_energy if max_energy else 0
            node.instrumentalness_dimention = track.instrumentalness / max_instrumentalness if max_instrumentalness else 0
            node.tempo_dimention = track.tempo / max_tempo if max_tempo else 0
            node.valence_dimention = track.valence / max_valence if max_valence else 0
            node.danceability_dimention = track.danceability / max_danceability if max_danceability else 0
            self.nodes.append(node)

    def _distance(self, node1: TrackNode, node2: TrackNode) -> float:
        # Calculate distance considering only relevant dimensions
        distance = 0
        if self.loudness_relevant:
            distance += (node1.loudness_dimention - node2.loudness_dimention) ** 2
        if self.energy_relevant:
            distance += (node1.energy_dimention - node2.energy_dimention) ** 2
        if self.instrumentalness_relevant:
            distance += (node1.instrumentalness_dimention - node2.instrumentalness_dimention) ** 2
        if self.tempo_relevant:
            distance += (node1.tempo_dimention - node2.tempo_dimention) ** 2
        if self.valence_relevant:
            distance += (node1.valence_dimention - node2.valence_dimention) ** 2
        if self.danceability_relevant:
            distance += (node1.danceability_dimention - node2.danceability_dimention) ** 2
        return math.sqrt(distance)

    def build_graph(self):
        for node in self.nodes:
            distances = []
            for other_node in self.nodes:
                if other_node is not node:
                    distance = self._distance(node, other_node)
                    distances.append((distance, other_node))
            distances.sort(key=lambda x: x[0])
            for _, closest_node in distances[:2]:
                if closest_node not in node.neighbours:
                    node.neighbours.add(closest_node)
                    if node not in closest_node.neighbours:
                        closest_node.neighbours.add(node)

        self._ensure_connectivity()

    def _ensure_connectivity(self):
        # Perform DFS to check connectivity
        visited = set()
        to_visit = [self.nodes[0]] if self.nodes else []

        while to_visit:
            current = to_visit.pop()
            if current not in visited:
                visited.add(current)
                to_visit.extend(neighbour for neighbour in current.neighbours if neighbour not in visited)

        # Add extra neighbours if the graph is not fully connected
        # and connect the unvisited node to the closest visited node
        if len(visited) != len(self.nodes):
            unvisited = [node for node in self.nodes if node not in visited]
            for unvisited_node in unvisited:
                distances = []
                for visited_node in visited:
                    distance = self._distance(unvisited_node, visited_node)
                    distances.append((distance, visited_node))
                distances.sort(key=lambda x: x[0])

                if distances:
                    _, closest_visited_node = distances[0]
                    unvisited_node.neighbours.add(closest_visited_node)
                    closest_visited_node.neighbours.add(unvisited_node)
                    visited.add(unvisited_node)


# Check the graph structure
def print_graph(graph):
    print("Track Graph")
    print("===========")
    for node in graph.nodes:
        print(f"Track ID: {node.track.name}")
        print(f"neighbours: {[neighbour.track.name for neighbour in node.neighbours]}")
        print("")


# Function to check connectivity
def is_connected(graph):
    visited = set()
    to_visit = [graph.nodes[0]] if graph.nodes else []

    while to_visit:
        current = to_visit.pop()
        if current not in visited:
            visited.add(current)
            to_visit.extend(neighbour for neighbour in current.neighbours if neighbour not in visited)

    return len(visited) == len(graph.nodes)

if __name__ == '__main__':
    playlist_id = processing_functions.get_playlist_id_from_url('https://open.spotify.com/playlist/05BoR0n9Ehp1hSE4KtRYjy?si=3ce3ea1b4cd0456d')
    pl = Playlist(sp.playlist(playlist_id))

    # Create graph
    graph = TracksGraph(pl)
    # Print the graph
    print_graph(graph)

    # Check if the graph is connected
    connected = is_connected(graph)
    print("Is graph fully connected?", connected)





