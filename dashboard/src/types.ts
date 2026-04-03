export interface GameItem {
  title: string;
  link: string;
  end_date: string;
  description: string;
  thumbnail: string;
}

export interface GamesHistoryResponse {
  games: GameItem[];
  total: number;
  limit: number;
  offset: number;
}

export type SortField = 'title' | 'end_date';
export type SortDirection = 'asc' | 'desc';
