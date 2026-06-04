'use client';

import {useState} from 'react';
import {useMutation} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {Check, Diamond, Loader, Search} from 'lucide-react';

function NFTInner() {
  const [searchArticleId, setSearchArticleId] = useState('');
  const [nftInfo, setNftInfo] = useState<any>(null);
  const [nftError, setNftError] = useState('');

  const searchNft = async () => {
    if (!searchArticleId) return;
    setNftInfo(null); setNftError('');
    try {
      const r = await apiClient.get(`/ext/nft/${searchArticleId}`);
      if (r.success && r.data) setNftInfo(r.data);
      else setNftError(r.error || '未找到 NFT 信息' || '查询失败');
    } catch { setNftError('查询失败'); }
  };

  // Mint form
  const [mintArticleId, setMintArticleId] = useState('');
  const [mintAddress, setMintAddress] = useState('');
  const [mintResult, setMintResult] = useState<any>(null);
  const mintMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/ext/nft/mint', data),
    onSuccess: (r) => { if (r.success) setMintResult(r.data); else setMintResult({error: r.error}); },
    onError: () => setMintResult({error: '铸造失败'}),
  });

  const clearMint = () => { setMintArticleId(''); setMintAddress(''); setMintResult(null); };

  return (
    <AdminShell title="NFT 管理">
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Mint NFT */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2"><Diamond className="w-5 h-5"/>铸造 NFT</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">文章 ID</label>
              <input type="number" value={mintArticleId} onChange={e => setMintArticleId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white"/>
            </div>
            <div>
              <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">所有者钱包地址</label>
              <input value={mintAddress} onChange={e => setMintAddress(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white font-mono" placeholder="0x..."/>
            </div>
            <button onClick={() => mintMut.mutate({article_id: parseInt(mintArticleId), owner_address: mintAddress})}
              disabled={mintMut.isPending || !mintArticleId || !mintAddress}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg inline-flex items-center gap-1.5 disabled:opacity-50">
              {mintMut.isPending ? <Loader className="w-4 h-4 animate-spin"/> : <Diamond className="w-4 h-4"/>}
              铸造
            </button>
            {mintResult && (
              <div className={`p-4 rounded-xl text-sm ${mintResult.error ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-700'}`}>
                {mintResult.error ? (
                  <p className="flex items-center gap-1"><Check className="w-4 h-4"/>{mintResult.error}</p>
                ) : (
                  <div className="space-y-1">
                    <p className="font-medium">铸造成功</p>
                    <p className="text-xs">Token ID: {mintResult.token_id || '—'}</p>
                    <p className="text-xs break-all">合约: {mintResult.contract_address ? `${mintResult.contract_address.slice(0, 20)}...` : '—'}</p>
                    <p className="text-xs break-all">所有者: {mintResult.owner_address ? `${mintResult.owner_address.slice(0, 20)}...` : '—'}</p>
                  </div>
                )}
                <button onClick={clearMint} className="text-xs mt-2 underline">清除</button>
              </div>
            )}
          </div>
        </div>

        {/* Query NFT */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2"><Search className="w-5 h-5"/>查询 NFT</h3>
          <div className="space-y-4">
            <div className="flex gap-3">
              <input type="number" value={searchArticleId} onChange={e => setSearchArticleId(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white" placeholder="文章 ID"/>
              <button onClick={searchNft}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg">查询</button>
            </div>
            {nftInfo && (
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-2 text-sm">
                <p><span className="text-gray-500 dark:text-gray-400">Token ID:</span> {nftInfo.token_id || '—'}</p>
                <p className="break-all"><span
                  className="text-gray-500 dark:text-gray-400">合约:</span> {nftInfo.contract_address || '—'}</p>
                <p className="break-all"><span
                  className="text-gray-500 dark:text-gray-400">所有者:</span> {nftInfo.owner_address || '—'}</p>
                <p><span className="text-gray-500 dark:text-gray-400">网络:</span> {nftInfo.network || '—'}</p>
                {nftInfo.transaction_hash && (
                  <p className="break-all"><span
                    className="text-gray-500 dark:text-gray-400">Tx:</span> {nftInfo.transaction_hash.slice(0, 30)}...
                  </p>
                )}
              </div>
            )}
            {nftError && <p className="text-sm text-red-500">{nftError}</p>}
          </div>
        </div>
      </div>
    </AdminShell>
  );
}

export default function ExtNFT() { return <AuthGuard><QueryProvider><NFTInner/></QueryProvider></AuthGuard>; }
